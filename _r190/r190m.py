#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R190 M：本轮全部核心数字的收敛复算（主会话自写，含正反控）。

回答四件事：
  M2/M3  vtable 层偏移集合与 RTTI 基类 PMD.mdisp 集合的关系（10 vs 14，差集 = 无副表的基类子对象）
  M4/M5  调整器 thunk 的位移规则：K == 本层 mdisp − 目标层 mdisp（305/305）
  M6-M9  三个固定层的表形（layer 12/8/4 的槽数与默认实现复用率）
  M10/M11 94 个同名多表组的地址序 vs 基类数组首现索引序（两条判据同源）
"""
import sys, os, struct, collections, json, capstone
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_r185'))
import pe185 as P

fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
COLS = {}
for sec in ('.rdata', '.data'):
    s = P.B[sec]; nd = s['rawsize'] // 4
    v = struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr'])
    for i in range(nd - 4):
        b = s['lo'] + 4 * i; d = v[i:i + 5]
        if d[0] not in (0, 1) or d[2] != 0: continue
        if P.where(d[3]) != '.data' or P.where(d[4]) != '.rdata': continue
        nm = P.cstr(d[3] + 8, 200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COLS[b] = dict(off=d[1], ptd=d[3], pchd=d[4], name=nm.decode('latin1'))
VTS = {}
for sec in ('.rdata', '.data'):
    s = P.B[sec]; nd = s['rawsize'] // 4
    v = struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr'])
    for i, x in enumerate(v):
        if not (LO <= x < HI): continue
        b = s['lo'] + 4 * i
        if P.dw(b - 4) in COLS: VTS[b] = COLS[P.dw(b - 4)]
def pre(vt):
    k = 0
    while True:
        d = P.dw(vt + 4 * k)
        if d is None or not (LO <= d < HI): return k
        k += 1
PRE = {vt: pre(vt) for vt in VTS}
order = sorted(VTS)
byname = collections.defaultdict(list)
for vt in order: byname[VTS[vt]['name']].append(vt)
mult = {k: v for k, v in byname.items() if len(v) > 1}
def bases(c):
    ch = c['pchd']; num = P.dw(ch + 8); pba = P.dw(ch + 12)
    return [(P.dw(e), P.dw(e + 4), P.dw(e + 8), P.dw(e + 12), P.dw(e + 16), P.dw(e + 20))
            for e in (P.dw(pba + 4 * j) for j in range(num))]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True
def adjdec(va):
    """sub dword ptr [esp+4], K ; jmp t   -> (K, t) ; else None（只解 16 B，不开全段）"""
    o = P.r2o(va)
    if o is None: return None
    ins = list(md.disasm(P.RAW[o:o + 16], va))
    if len(ins) < 2: return None
    a, c = ins[0], ins[1]
    if a.mnemonic != 'sub' or 'esp + 4' not in a.op_str: return None
    try: k = a.operands[1].imm
    except Exception: return None
    if c.mnemonic != 'jmp' or not c.op_str.startswith('0x'): return None
    return (k, int(c.op_str, 16))

ck('M0 COL 1214 / vtable 1214 / 槽位实例 14044',
   (len(COLS), len(VTS), sum(PRE.values())) == (1214, 1214, 14044), (len(COLS), len(VTS), sum(PRE.values())))
ck('M1 1214 张表指向的 COL 记录两两不同', len(set(P.dw(vt - 4) for vt in order)) == 1214)
layeroffs = set(c['off'] for c in COLS.values())
bmds = set(b[2] for c in COLS.values() for b in bases(c))
ck('M2 vtable 层偏移集合 = {0,4,8,12,24,36,40,44,1728,21784}（10 个）',
   layeroffs == {0, 4, 8, 12, 24, 36, 40, 44, 1728, 21784}, sorted(layeroffs))
ck('M3 基类描述符 PMD.mdisp 集合 = 上面 10 个 + {172,176,240,248}（14 个）',
   bmds == {0, 4, 8, 12, 24, 36, 40, 44, 172, 176, 240, 248, 1728, 21784}, sorted(bmds))
ck('M3b 层偏移集合是 PMD.mdisp 集合的真子集，差集 = {172,176,240,248}',
   layeroffs < bmds and bmds - layeroffs == {172, 176, 240, 248}, sorted(bmds - layeroffs))
for m in sorted(bmds - layeroffs):
    who = collections.Counter(P.cstr(b[0] + 8, 60).decode('latin1')
                              for c in COLS.values() for b in bases(c) if b[2] == m)
    print('#  mdisp=%d 基类项 %d 条，宿主类 top3=%s' % (m, sum(who.values()), who.most_common(3)))

nz = [vt for vt in order if VTS[vt]['off'] != 0]
byvt = {}
for nm, lst in mult.items():
    for vt in lst: byvt[vt] = lst
tot = 0; adj = 0; ruleok = 0; bad = []
for vt in nz:
    lst = byvt[vt]; m = VTS[vt]['off']
    for k in range(PRE[vt]):
        tot += 1; r = adjdec(P.dw(vt + 4 * k))
        if r is None: continue
        adj += 1
        t = None
        for c2 in lst:
            if c2 == vt: continue
            if k < PRE[c2] and P.dw(c2 + 4 * k) == r[1]: t = c2; break
        if t is None: bad.append(('no-target', VTS[vt]['name'][:28], m, k)); continue
        if r[0] == m - VTS[t]['off']: ruleok += 1
        else: bad.append(('K-mismatch', VTS[vt]['name'][:28], m, k, r[0], m - VTS[t]['off']))
ck('M4 非主表（mdisp!=0）共 %d 槽，其中调整器 thunk %d 个' % (tot, adj), tot == 1318 and adj == 305, (tot, adj))
ck('M5 调整器规则 K == 本层 mdisp − 目标层 mdisp：%d/%d 成立，反例 %d' % (ruleok, adj, len(bad)),
   ruleok == adj and len(bad) == 0, (ruleok, len(bad)))
ck('M6 layer 12 的 78 张全部 1 槽且槽 0 == 0x410590（ret 4）',
   sum(1 for vt in order if VTS[vt]['off'] == 12) == 78 and
   all(PRE[vt] == 1 and P.dw(vt) == 0x410590 for vt in order if VTS[vt]['off'] == 12))
g8 = [vt for vt in order if VTS[vt]['off'] == 8]
ck('M7 layer 8 的 78 张全部 1 槽；75 张槽 0 == 0x410580（xor al,al;ret 8），3 张真实现覆盖',
   len(g8) == 78 and all(PRE[vt] == 1 for vt in g8) and sum(1 for vt in g8 if P.dw(vt) == 0x410580) == 75,
   (len(g8), sum(1 for vt in g8 if P.dw(vt) == 0x410580), [hex(vt) for vt in g8 if P.dw(vt) != 0x410580]))
g4 = [vt for vt in order if VTS[vt]['off'] == 4]
ck('M8 layer 4 的 91 张槽数分布 {5:1, 6:78, 50:12}；50 槽的 12 张全是 Locomotion 派生',
   collections.Counter(PRE[vt] for vt in g4) == collections.Counter({5: 1, 6: 78, 50: 12}) and
   all('LocomotionClass' in VTS[vt]['name'] for vt in g4 if PRE[vt] == 50))
pat = collections.Counter(tuple(P.dw(vt + 4 * k) for k in range(PRE[vt])) for vt in g4 if PRE[vt] == 6)
ck('M9 layer 4 的 78 张 6 槽表中 72 张共用同一组 6 个默认实现', pat.most_common(1)[0][1] == 72,
   (pat.most_common(1)[0][1], len(pat)))
det = []; ok = 0; bad2 = []
for nm, lst in mult.items():
    prim = [vt for vt in lst if VTS[vt]['off'] == 0][0]; bs = bases(VTS[prim])
    firstidx = {}
    for j, b in enumerate(bs): firstidx.setdefault(b[2], j)
    idx = [firstidx.get(VTS[vt]['off']) for vt in lst]
    if nm in ('.?AVOverlayClass@@', '.?AVSmudgeClass@@', '.?AVTerrainClass@@'):
        det.append((nm, [VTS[vt]['off'] for vt in lst], idx))
    if None in idx: bad2.append((nm, 'missing', idx)); continue
    if all(idx[i] > idx[i + 1] for i in range(len(idx) - 1)): ok += 1
    else: bad2.append((nm, [VTS[vt]['off'] for vt in lst], idx))
ck('M10 94 组中「地址升序 ⇒ 基类数组首现索引严格递减」满足 %d，反例 %d（恰为 mdisp 那 3 组）' % (ok, len(bad2)),
   ok == 91 and len(bad2) == 3, [b[0] for b in bad2])
for d in det: print('#  %s 层偏移 %s → 基类数组首现索引 %s' % (d[0], d[1], d[2]))
# 反控：判据反过来（地址升序要求索引递增）
okrev = 0
for nm, lst in mult.items():
    prim = [vt for vt in lst if VTS[vt]['off'] == 0][0]; bs = bases(VTS[prim])
    firstidx = {}
    for j, b in enumerate(bs): firstidx.setdefault(b[2], j)
    idx = [firstidx.get(VTS[vt]['off']) for vt in lst]
    if None in idx: continue
    if all(idx[i] < idx[i + 1] for i in range(len(idx) - 1)): okrev += 1
ck('N1 反控：把判据反向（要求首现索引递增）满足 %d 组（应 0）' % okrev, okrev == 0, okrev)
json.dump(dict(layeroffs=sorted(layeroffs), bmds=sorted(bmds), extra=sorted(bmds - layeroffs),
               adj=adj, ruleok=ruleok, nzslots=tot, layer8=len(g8),
               layer8_def=sum(1 for vt in g8 if P.dw(vt) == 0x410580),
               layer4=dict((str(k), v) for k, v in sorted(collections.Counter(PRE[vt] for vt in g4).items())),
               pat6=pat.most_common(1)[0][1], pat6_kinds=len(pat),
               order_examples=[(d[0], d[1], d[2]) for d in det], order_ok=ok, order_rev=okrev),
          open(os.path.join(HERE, 'r190m.json'), 'w'), indent=1, ensure_ascii=False)
print('\n断言 %d 条，FAIL %d 条' % (N, len(fails)))
sys.exit(1 if fails else 0)
