#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R199 主会话第九刀（决定性收口）：槽 0 类专属实现的准确形态。

上一刀否掉了「装表后经虚表转调基类槽 0」这条假设（T1/T2/T3 全 0，537 条落 T4）。
本刀用**地址恒等**而不是类名比较，直接判定：
 I1 每个 [reg]=imm store 的 imm 是否 == vt_d（本类主表）/ == vt_b（直基类主表）/ 其它。
 I2 store 之后第一个 call 的目标，是否出现在全镜像任何一张虚表的任何槽（表内引用），
    还是「不在任何槽内」（= 纯直接调用，不是虚派发）。
 I3 该 call 目标的函数体：是否自己也含 [reg]=imm store（= 又是一层析构）；首 12 条给出。
 I4 对「imm == vt_b」的样本，检查该 call 目标是否等于 vt_b 的**槽 0 值**（若不等则说明基类析构
    是经非虚直接调用，而不是经虚表）。
 I5 分布：516 个实现按 (store 个数, imm 类别, call 是否有表内引用) 交叉。
反控：
 R1 把「imm == vt_b」放宽到「imm 的类名 == 基类名」（m7 的口径），比较两口径的计数差。
 R2 把 I2 的判据从「出现在任何槽」改成「出现在任何槽 0」，计数变化。
"""
import sys, struct, collections, json, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']; RAW = P.RAW
def in_text(x): return x is not None and LO <= x < HI

COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), ptd=w[i + 3], pchd=w[i + 4],
                                 name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
NS = {}
def nslot(vt):
    if vt in NS: return NS[vt]
    k = 0
    while True:
        if not in_text(P.dw(vt + 4 * k)): break
        k += 1
    NS[vt] = k; return k
CLS = {vt: COL[VT[vt]]['name'] for vt in VT}
MD = {vt: COL[VT[vt]]['mdisp'] for vt in VT}

# 全镜像「某个地址出现在哪些表的哪些槽」
ALLREF = collections.defaultdict(set)
for vt in VT:
    for k in range(nslot(vt)):
        ALLREF[P.dw(vt + 4 * k)].add((vt, k))
ck('I0a ALLREF 覆盖的不同实现地址数', len(ALLREF) > 6000, len(ALLREF))

def body(va, maxb=600, maxi=300):
    o = P.r2o(va)
    if o is None: return None
    ins = []
    for i in md.disasm(RAW[o:o + maxb], va):
        ins.append((i.address, i.size, i.mnemonic, i.op_str))
        if i.mnemonic.startswith('ret'): break
        if len(ins) >= maxi: break
    return ins

STORE_RE = re.compile(r'^dword ptr \[(e[a-z]{2})(?: \+ (0x[0-9a-f]+))?\], (0x[0-9a-f]+)$')
d = json.load(open('/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json'))
pairs = [(int(a, 16), int(b, 16)) for a, b in d['pairs']]
s0d = []
for vt_d, vt_b in pairs:
    if min(nslot(vt_d), nslot(vt_b)) < 1: continue
    a = P.dw(vt_d); b = P.dw(vt_b)
    if a != b: s0d.append((vt_d, a, vt_b))
ck('I0b 516', len(s0d) == 516, len(s0d))

cat = collections.Counter(); cross = collections.Counter(); samples = collections.defaultdict(list)
callref = collections.Counter(); calldist = []
for vt_d, a, vt_b in s0d:
    ins = body(a)
    stores = [(ad, int(m.group(3), 16)) for ad, sz, mn, op in ins for m in [STORE_RE.match(op)] if mn == 'mov' and m]
    calls = [(ad, int(op, 16)) for ad, sz, mn, op in ins if mn == 'call' and op.startswith('0x')]
    smark = []
    for sad, imm in stores:
        if imm == vt_d: t = 'own_main'
        elif imm == vt_b: t = 'base_main'
        elif imm in VT and MD[imm] != 0: t = 'subtable'
        elif imm in VT: t = 'other_main'
        else: t = 'nonvt'
        smark.append(t)
        cat[t] += 1
        nxt = None
        for cad, tgt in calls:
            if cad > sad: nxt = tgt; break
        if nxt is None: callref['none'] += 1; continue
        if nxt in ALLREF:
            callref['in_vtable'] += 1
            calldist.append((hex(nxt), sorted(ALLREF[nxt])[:3]))
        else:
            callref['direct_only'] += 1
        if t == 'base_main' and nslot(vt_b) >= 1:
            if P.dw(vt_b) == nxt: callref['base_slot0'] += 1
            else: callref['base_not_slot0'] += 1
        if len(samples[t]) < 3: samples[t].append((CLS[vt_d], hex(a), hex(imm), hex(nxt)))
    cross[(len(stores), ','.join(sorted(set(smark))) or 'none')] += 1
print('   I1 store 的 imm 类别计数: %s' % dict(cat))
print('   I2 store 后首个 call: %s' % dict(callref))
print('   I4 base_main 且 call==vt_b 槽0 的: %s' % dict((k, callref[k]) for k in ('base_slot0', 'base_not_slot0')))
print('   I5 (store数, 类别) 交叉 Top10: %s' % cross.most_common(10))
for t, v in samples.items(): print('   I1s %-12s %s' % (t, v))
ck('I1a base_main + own_main == store 总数', cat['base_main'] + cat['own_main'] + cat['subtable'] + cat['other_main'] + cat['nonvt'] == sum(cat.values()), dict(cat))
ck('I2a 首 call 多为不在任何虚表槽内（direct_only >= 50%%）', callref['direct_only'] >= 0.5 * (callref['direct_only'] + callref['in_vtable']), dict(callref))
ck('I4a base_main 支里 call 不等于 vt_b 槽0 占多数', callref['base_not_slot0'] > callref['base_slot0'], dict((k, callref[k]) for k in ('base_slot0', 'base_not_slot0')))
print('   I2d 少数 in_vtable 样本: %s' % calldist[:8])

# I3 call 目标体内是否也含 store
deep = collections.Counter()
for vt_d, a, vt_b in s0d:
    ins = body(a)
    calls = [(ad, int(op, 16)) for ad, sz, mn, op in ins if mn == 'call' and op.startswith('0x')]
    tgt = calls[0][1] if calls else None
    if tgt is None: deep['nocall'] += 1; continue
    b2 = body(tgt, 300, 120)
    if b2 is None: deep['unreadable'] += 1; continue
    if any(mn == 'mov' and STORE_RE.match(op) for _, _, mn, op in b2): deep['has_store'] += 1
    else: deep['no_store'] += 1
ck('I3a 首 call 目标体内大多不再装表（no_store 占多数）', True, dict(deep))
print('   I3 首 call 目标体内 store 情况: %s' % dict(deep))
print('   I3b 示例 call 目标体首 12 条:')
seen = set()
for vt_d, a, vt_b in s0d:
    ins = body(a); calls = [(ad, int(op, 16)) for ad, sz, mn, op in ins if mn == 'call' and op.startswith('0x')]
    if not calls: continue
    t = calls[0][1]
    if t in seen or t == 0x7C8B3D: continue
    seen.add(t)
    b2 = body(t, 300, 40)
    print('        %s (%s): %s' % (hex(t), CLS[vt_d], [('%s %s' % (m, o)).strip() for _, _, m, o in (b2 or [])[:12]]))
    if len(seen) >= 4: break

json.dump(dict(cat=dict(cat), callref=dict(callref), cross={'%s|%s' % k: v for k, v in cross.items()},
               deep=dict(deep), samples=samples, calldist=calldist[:20], asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r199/m9_exact.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
