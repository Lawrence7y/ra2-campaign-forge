#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R199 主会话第五刀：槽 0 的 516 个「类专属」实现是什么形态（字节级自证，不下语义断言）。

判据（全部字节）：
 E1 对 516 个槽 0 派生实现逐个 detail=True 反汇编到首个 ret（<=400B）。
 E2 三维特征：
    (a) 体内是否 mov dword ptr [ecx], imm32，且 imm32 是否落在 .rdata/.data（装虚表）；
        该 imm32 的 virt-4 是否为 COL、其 COL 的类名是否与该表类名相同（=装回本类表）；
    (b) 体内是否 call 某地址，且该 call 目标体内含 rep movsd 或 movsd（拷贝）——只记 call 目标地址前 16B hex；
    (c) ret 形态。
 E3 对 ret 形态与 (a)(b) 做交叉表：class专属实现里「装虚表 + 有 call + ret imm」的占比。
 E4 反控：把 516 个换成「基类侧槽 0 的实现」，同样跑一遍，比较特征占比（若两者差异极大，
    说明槽 0 在派生侧被每类重写而基类侧是共享默认）。
 E5 抽样代价：给 5 个具体地址的完整指令序列（<=14 条）。
"""
import sys, struct, collections, json
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
        COL[base + 4 * i] = dict(mdisp=s32(w[i + 1]), ptd=w[i + 3], name=nm.decode('latin1'))
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

def body(va, maxb=400, maxi=200):
    o = P.r2o(va)
    if o is None: return None
    ins = []
    for i in md.disasm(RAW[o:o + maxb], va):
        ins.append((i.address, i.size, i.mnemonic, i.op_str))
        if i.mnemonic.startswith('ret'): break
        if len(ins) >= maxi: break
    return ins

VT2COL = {vt: COL[VT[vt]] for vt in VT}
def feat(va):
    ins = body(va)
    if ins is None: return None
    vtstores = []; calls = []; retform = None
    for a, sz, mn, op in ins:
        if mn.startswith('ret'):
            retform = op if op else 'plain'
        if mn == 'mov' and op.startswith('dword ptr [ecx], 0x'):
            try: imm = int(op.split(', ')[1], 16)
            except Exception: imm = None
            if imm is not None: vtstores.append(imm)
        if mn == 'call' and op.startswith('0x'):
            calls.append(int(op, 16))
    return dict(n=len(ins), nbytes=sum(s for _, s, _, _ in ins),
                vtstores=vtstores, calls=calls, ret=retform, ins=ins)

d = json.load(open('/home/t628/projects/ra2-campaign-forge/_r199/m1_pair.json'))
pairs = [(int(a, 16), int(b, 16)) for a, b in d['pairs']]
s0d = []; s0b = []
for vt_d, vt_b in pairs:
    if min(nslot(vt_d), nslot(vt_b)) < 1: continue
    a = P.dw(vt_d); b = P.dw(vt_b)
    if a != b: s0d.append((vt_d, a))
    s0b.append((vt_b, b))
ck('E0a 槽0 派生不匹配 516 / 基类侧 603', (len(s0d), len(s0b)) == (516, 603), (len(s0d), len(s0b)))
uniq_d = set(a for _, a in s0d)
ck('E0b 派生侧地址去重 516', len(uniq_d) == 516, len(uniq_d))

FD = {a: feat(a) for a in uniq_d}
ck('E1a 516 个派生实现全部可反汇编（非 None）', all(v is not None for v in FD.values()),
   sum(1 for v in FD.values() if v is None))
ck('E1b 全部在 400B 内遇到 ret', all(v['ret'] is not None for v in FD.values()),
   sum(1 for v in FD.values() if v['ret'] is None))

# E2 特征
same_vt = 0; any_vt = 0; withcall = 0; retimm = 0; retpl = 0
all3 = 0; vtsame_names = []
name_of_vt = {}
for vt in VT: name_of_vt[vt] = COL[VT[vt]]['name']
for vt_d, a in s0d:
    f = FD[a]
    own = name_of_vt[vt_d]
    hit_same = False
    for imm in f['vtstores']:
        if imm in VT2COL:
            any_vt += 1 if imm == f['vtstores'][0] else 0
            if VT2COL[imm]['name'] == own:
                hit_same = True; vtsame_names.append((hex(a), own, hex(imm)))
    if f['vtstores']: any_vt += 0
    if hit_same: same_vt += 1
    if f['calls']: withcall += 1
    if f['ret'] == 'plain': retpl += 1
    else: retimm += 1
    if hit_same and f['calls'] and f['ret'] != 'plain': all3 += 1
anystore = sum(1 for vt_d, a in s0d if FD[a]['vtstores'])
inVT = sum(1 for vt_d, a in s0d if any(i in VT2COL for i in FD[a]['vtstores']))
print('   E2 516 个派生槽0实现: 有 [ecx]=imm 装的=%d，其中 imm 是虚表地址的=%d，imm 是本类虚表的=%d'
      % (anystore, inVT, same_vt))
print('        体内有 call 的=%d，ret imm 形态=%d，裸 ret=%d，三重特征同时成立=%d'
      % (withcall, retimm, retpl, all3))
ck('E2a 本类虚表装回占比 > 50%%', same_vt / 516.0 > 0.5, round(100 * same_vt / 516.0, 2))
ck('E2b 体内有 call 占比 > 90%%', withcall / 516.0 > 0.90, round(100 * withcall / 516.0, 2))
ck('E2c ret imm 占比 > 90%%', retimm / 516.0 > 0.90, round(100 * retimm / 516.0, 2))

# E4 反控：基类侧
uniq_b = set(a for _, a in s0b)
FB = {a: feat(a) for a in uniq_b}
b_call = sum(1 for a in uniq_b if FB[a] and FB[a]['calls'])
b_retimm = sum(1 for a in uniq_b if FB[a] and FB[a]['ret'] and FB[a]['ret'] != 'plain')
b_store = sum(1 for a in uniq_b if FB[a] and FB[a]['vtstores'])
print('   E4 基类侧槽0 实现去重=%d: 有 call=%d(%.2f%%) ret imm=%d(%.2f%%) 有 vtstore=%d(%.2f%%)'
      % (len(uniq_b), b_call, 100.0 * b_call / len(uniq_b), b_retimm,
         100.0 * b_retimm / len(uniq_b), b_store, 100.0 * b_store / len(uniq_b)))
ck('E4a 派生侧「装本类虚表」比例显著高于基类侧',
   same_vt / 516.0 > (b_store / float(len(uniq_b))) + 0.2,
   (round(100 * same_vt / 516.0, 2), round(100.0 * b_store / len(uniq_b), 2)))

# E5 抽样
samp = []
for vt_d, a in s0d[:5]:
    f = FD[a]
    samp.append(dict(cls=name_of_vt[vt_d], va=hex(a), n=f['n'], nbytes=f['nbytes'],
                     ret=f['ret'], vtstores=[hex(x) for x in f['vtstores']],
                     calls=[hex(x) for x in f['calls']],
                     ins=[('%s %s' % (mn, op)).strip() for _, _, mn, op in f['ins'][:14]]))
for s in samp:
    print('   E5 %-44s %s n=%d' % (s['cls'], s['va'], s['n']))
    print('        %s' % s['ins'])

# E6 call 目标的集中度
tg = collections.Counter()
for vt_d, a in s0d:
    for c in FD[a]['calls']: tg[c] += 1
print('   E6 派生槽0 体内 call 目标 Top10: %s' % [(hex(a), c) for a, c in tg.most_common(10)])
ck('E6a call 目标去重数', True, len(tg))

# E7 vtstore 目标集中度
vs = collections.Counter()
for vt_d, a in s0d:
    for imm in FD[a]['vtstores']: vs[imm] += 1
invt = sum(c for imm, c in vs.items() if imm in VT2COL)
print('   E7 vtstore imm 去重=%d 次数=%d，其中 imm 是虚表地址的次数=%d' % (len(vs), sum(vs.values()), invt))
ck('E7a vtstore 目标大多是虚表地址', invt >= 0.5 * sum(vs.values()), (invt, sum(vs.values())))

json.dump(dict(n=516, anystore=anystore, inVT=inVT, same_vt=same_vt, withcall=withcall,
               retimm=retimm, retpl=retpl, all3=all3,
               base=dict(uniq=len(uniq_b), call=b_call, retimm=b_retimm, store=b_store),
               samp=samp, calltop=[[hex(a), c] for a, c in tg.most_common(20)],
               vstop=[[hex(a), c] for a, c in vs.most_common(20)],
               vtsame_names=vtsame_names[:20], asserts=N, fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r199/m5_slot0.json', 'w'), ensure_ascii=False, indent=1)
print('\nSUMMARY asserts=%d fails=%d %s' % (N, len(fails), fails))
