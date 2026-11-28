#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R199 主会话第八刀（决定性）：槽 0 类专属实现的确切形态 —— 装哪张表、紧接着调谁。

上一刀 H4 假设「装表后调该表槽 0」命中 0/427，说明假设错。本刀用完整函数体打印 12 例，
并同时检验 4 个互斥假设，看哪一个成立：
 T1 call 目标 == 被装表 vt_x 的槽 0 值
 T2 call 目标 == 本类表 vt_d 的槽 0 值（自己，不可能）
 T3 call 目标 == 被装表 vt_x 槽 0 的**基类侧同槽实现**（沿 RTTI 继续上溯一跳）
 T4 call 目标与任何表的槽 0 都无关（是独立的全镜像唯一函数）
另做 B 侧复核（执行员 B 的数字）：
 B1 0x4C9150 覆盖 33 槽号 / 39 表 / 205 槽位
 B2 全 .text 字节扫 33 C0 C3 的命中数（执行员报 249）
 B3 被虚表引用的零桩地址个数（执行员报 27）
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
PTD = {vt: COL[VT[vt]]['ptd'] for vt in VT}

CHD = {}
for c, cc in COL.items():
    v = cc['pchd']
    if v in CHD: continue
    CHD[v] = dict(n=P.dw(v + 8), arr=P.dw(v + 12))
BCDS = {}
for v, d in CHD.items():
    arr = d['arr']; lst = None
    if P.where(arr) not in ('None', 'other') and d['n'] is not None and 0 < d['n'] <= 64:
        lst = [P.dw(arr + 4 * j) for j in range(d['n'])]
        if any(x is None for x in lst): lst = None
    d['bcds'] = lst
    for b in (lst or []):
        BCDS[b] = dict(ptd=P.dw(b), ncb=P.dw(b + 4), mdisp=s32(P.dw(b + 8)), chd=v)
def direct_children(bcds, i):
    out = []; n = len(bcds); lim = i + BCDS[bcds[i]]['ncb']; j = i + 1
    while j <= lim and j < n:
        out.append(j); j = j + BCDS[bcds[j]]['ncb'] + 1
    return out

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
ck('T0a 槽0 派生不匹配 516', len(s0d) == 516, len(s0d))

# 打印 12 例完整体
print('   --- 12 例完整函数体 ---')
for vt_d, a, vt_b in s0d[:12]:
    ins = body(a)
    print('   %s %s  (基类 %s)' % (CLS[vt_d], hex(a), CLS[vt_b]))
    print('        %s' % [('%s %s' % (m, o)).strip() for _, _, m, o in ins])

# 三假设检验
res = collections.Counter(); samples = collections.defaultdict(list)
for vt_d, a, vt_b in s0d:
    ins = body(a); own = CLS[vt_d]
    calls = [(ad, int(op, 16)) for ad, sz, mn, op in ins if mn == 'call' and op.startswith('0x')]
    for ad, sz, mn, op in ins:
        if mn != 'mov': continue
        m = STORE_RE.match(op)
        if not m: continue
        imm = int(m.group(3), 16)
        if imm not in CLS: continue
        sad = ad
        nxt = None
        for (cad, tgt) in calls:
            if cad > sad: nxt = tgt; break
        if nxt is None: res['no_call_after'] += 1; continue
        if nslot(imm) >= 1 and P.dw(imm) == nxt: res['T1_slotX0'] += 1
        elif nslot(vt_d) >= 1 and P.dw(vt_d) == nxt: res['T2_own0'] += 1
        elif nslot(vt_b) >= 1 and P.dw(vt_b) == nxt: res['T3_basePanel0'] += 1
        else:
            res['T4_other'] += 1
            if len(samples['T4']) < 8: samples['T4'].append((own, hex(a), CLS.get(imm, '?'), hex(nxt)))
print('   T1/T2/T3/T4 分类: %s' % dict(res))
ck('T4a 三假设中恰一个占多数（>=70%%）', max(res.values()) >= 0.70 * sum(res.values()), dict(res))
print('   T4 例: %s' % samples['T4'])

# 直接核：call 目标是不是「被装表的槽 0 值之外，基类链上某张表的槽 0」
# 换一个绝不假设的口径：给 nxt 反查它出现在哪些表的哪个槽
nxt_where = collections.Counter()
targets = []
for vt_d, a, vt_b in s0d:
    ins = body(a)
    for ad, sz, mn, op in ins:
        if mn == 'call' and op.startswith('0x'):
            tgt = int(op, 16)
            if tgt not in (0x7C8B3D,): targets.append(tgt)
sid = collections.defaultdict(list)
for vt in VT:
    for k in range(nslot(vt)):
        sid[P.dw(vt + 4 * k)].append((vt, k))
cnt = collections.Counter()
for t in set(targets):
    ks = [k for vt, k in sid.get(t, [])]
    cnt[tuple(sorted(set(ks)))[:4]] += 1
print('   T5 非 delete-call 目标按其所在槽号组合计数 Top10: %s' % [(k, v) for k, v in cnt.most_common(10)])
only0 = sum(1 for t in set(targets) if set(k for vt, k in sid.get(t, [])) == {0})
noVT = sum(1 for t in set(targets) if t not in sid)
print('   T6 去重 call 目标=%d，其中只出现在槽 0 的=%d，不出现在任何表的=%d'
      % (len(set(targets)), only0, noVT))
ck('T6a 去重 call 目标数 > 0', len(set(targets)) > 0, len(set(targets)))

# B 侧复核
d2v = collections.defaultdict(set); d2s = collections.defaultdict(set)
for vt in VT:
    for k in range(nslot(vt)):
        t = P.dw(vt + 4 * k); d2v[t].add(vt); d2s[t].add(k)
slt = d2s[0x4C9150]; tlt = d2v[0x4C9150]
nslotcnt = sum(1 for vt in VT for k in range(nslot(vt)) if P.dw(vt + 4 * k) == 0x4C9150)
print('   B1 0x4C9150: 槽号种类=%d 表数=%d 槽位数=%d' % (len(slt), len(tlt), nslotcnt))
ck('B1a 33/39/205 复现', (len(slt), len(tlt), nslotcnt) == (33, 39, 205), (len(slt), len(tlt), nslotcnt))
bt = RAW[T['rawptr']:T['rawptr'] + (HI - LO)]
hits = [LO + i for i in range(len(bt) - 2) if bt[i:i + 3] == b'\x33\xc0\xc3']
print('   B2 全 .text 字节扫 33 C0 C3 命中=%d（执行员报 249）' % len(hits))
ck('B2a 249 复现', len(hits) == 249, len(hits))
ents = [h for h in hits if h == LO or bt[h - LO - 1] in (0x90, 0xC3, 0xC2, 0xCC)]
vtref = set(t for t in d2v if t in set(hits) or True)
zero_refs = [t for t, s in d2v.items() if t in set(hits)]
print('   B3 被虚表引用且体为 33 C0 C3 的地址=%d（执行员报 27）' % len(zero_refs))
ck('B3a 27 复现', len(zero_refs) == 27, len(zero_refs))

json.dump(dict(hyp=dict(res), T4_samples=samples['T4'],
               targets_uniq=len(set(targets)), only0=only0, noVT=noVT,
               b1=[len(slt), len(tlt), nslotcnt], b2=len(hits), b3=len(zero_refs),
               asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r199/m8_shape.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
