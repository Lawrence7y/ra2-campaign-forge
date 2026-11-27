#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R190 B：调整器 thunk 的位移规则 + 三个固定层的表形（主会话自写，含正反控）。

B1 非主表（COL.mdisp != 0）的槽里有多少是「sub dword ptr [esp+4], K ; jmp t」形态
B2 每个 thunk 的 jmp 目标是否等于同组另一张表**同槽号**的值
B3 规则检验：K == 本层 mdisp − 目标层 mdisp（而不是 K == 本层 mdisp）
B4 三个固定层的表形：layer 12 / layer 8 / layer 4 的槽数与默认实现复用率
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
        COLS[b] = dict(mdisp=d[1], ptd=d[3], name=nm.decode('latin1'))
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
byvt = {}
for nm, lst in mult.items():
    for vt in lst: byvt[vt] = lst
# 只在 16 B 小缓冲上开 detail=True，绝不对整段 .text 开
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True
def adjdec(va):
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

nz = [vt for vt in order if VTS[vt]['mdisp'] != 0]
tot = 0; adj = 0; sameidx = 0; ruleok = 0; bad = []
delta = collections.Counter()
for vt in nz:
    lst = byvt[vt]; m = VTS[vt]['mdisp']
    for k in range(PRE[vt]):
        tot += 1; r = adjdec(P.dw(vt + 4 * k))
        if r is None: continue
        adj += 1
        t = None
        for c2 in lst:
            if c2 == vt: continue
            if k < PRE[c2] and P.dw(c2 + 4 * k) == r[1]: t = c2; break
        if t is None: bad.append(('no-same-index-target', VTS[vt]['name'][:28], m, k)); continue
        sameidx += 1
        delta[(m, VTS[t]['mdisp'], r[0])] += 1
        if r[0] == m - VTS[t]['mdisp']: ruleok += 1
        else: bad.append(('K-mismatch', VTS[vt]['name'][:28], m, k, r[0], m - VTS[t]['mdisp']))
ck('B1 非主表共 %d 槽，其中调整器 thunk %d 个（其余 %d 是普通函数指针）' % (tot, adj, tot - adj),
   tot == 1318 and adj == 305, (tot, adj))
ck('B2 每个 thunk 的 jmp 目标都能定位到同组另一张表的同槽号：%d/%d' % (sameidx, adj), sameidx == adj, (sameidx, adj))
ck('B3 规则 K == 本层 mdisp − 目标层 mdisp：%d/%d 成立，反例 %d' % (ruleok, adj, len(bad)),
   ruleok == adj and len(bad) == 0, (ruleok, len(bad)))
print('#  (本层 mdisp → 目标层 mdisp, K) 直方:', dict(sorted(delta.items())))
prim = sum(v for (a, b, c), v in delta.items() if b == 0)
ck('B3b 目标层为 mdisp==0 主表的 %d 个，其余 %d 个（HouseClass 40→36）' % (prim, adj - prim),
   prim == 303 and adj - prim == 2, (prim, adj - prim))
c = sum(1 for vt in nz for k in range(PRE[vt])
        if (lambda r: r is not None and r[0] == VTS[vt]['mdisp'])(adjdec(P.dw(vt + 4 * k))))
ck('N1 反控：改用 K == 本层 mdisp 判等只命中 %d（< 305，HouseClass 那种层间转调被漏掉）' % c, c == 303, c)
c2 = sum(1 for vt in nz for k in range(PRE[vt])
         if (lambda r: r is not None and r[0] == VTS[vt]['mdisp'] - VTS[byvt[vt][0]]['mdisp'])(adjdec(P.dw(vt + 4 * k))))
ck('N2 反控：改用「本层 mdisp − 组内最低地址层 mdisp」命中 %d（应 0）' % c2, c2 == 0, c2)
# ---- 层形 ----
g12 = [vt for vt in order if VTS[vt]['mdisp'] == 12]
ck('B4 layer 12 的 78 张全部 1 槽且槽 0 == 0x410590（c2 04 00 = ret 4）',
   len(g12) == 78 and all(PRE[vt] == 1 and P.dw(vt) == 0x410590 for vt in g12), len(g12))
g8 = [vt for vt in order if VTS[vt]['mdisp'] == 8]
ck('B5 layer 8 的 78 张全部 1 槽；75 张槽 0 == 0x410580（32 c0 c2 08 00 = xor al,al; ret 8）',
   len(g8) == 78 and all(PRE[vt] == 1 for vt in g8) and sum(1 for vt in g8 if P.dw(vt) == 0x410580) == 75,
   (len(g8), sum(1 for vt in g8 if P.dw(vt) == 0x410580)))
odd8 = [(hex(vt), VTS[vt]['name']) for vt in g8 if P.dw(vt) != 0x410580]
ck('B5b layer 8 的 3 张例外都是具名（非模板）类，且槽 0 是真实现', len(odd8) == 3 and
   all('?$' not in n for _, n in odd8), odd8)
g4 = [vt for vt in order if VTS[vt]['mdisp'] == 4]
ck('B6 layer 4 的 91 张槽数分布 {5:1, 6:78, 50:12}',
   collections.Counter(PRE[vt] for vt in g4) == collections.Counter({5: 1, 6: 78, 50: 12}),
   sorted(collections.Counter(PRE[vt] for vt in g4).items()))
loco = [vt for vt in g4 if PRE[vt] == 50]
ck('B6b 50 槽的 12 张全部是 Locomotion 派生类', len(loco) == 12 and
   all('LocomotionClass' in VTS[vt]['name'] for vt in loco), len(loco))
pat = collections.Counter(tuple(P.dw(vt + 4 * k) for k in range(PRE[vt])) for vt in g4 if PRE[vt] == 6)
top = pat.most_common(1)[0]
ck('B7 layer 4 的 78 张 6 槽表中 %d 张共用同一组 6 个默认实现（共 %d 种组合）' % (top[1], len(pat)),
   top[1] == 72, (top[1], len(pat), [hex(x) for x in top[0]]))
json.dump(dict(nzslots=tot, adj=adj, sameidx=sameidx, ruleok=ruleok,
               delta=dict(('%d->%d K=%d' % k, v) for k, v in delta.items()),
               prim=prim, layer12=len(g12), layer8=len(g8),
               layer8_default=sum(1 for vt in g8 if P.dw(vt) == 0x410580), layer8_odd=odd8,
               layer4=dict((str(k), v) for k, v in sorted(collections.Counter(PRE[vt] for vt in g4).items())),
               pat6=top[1], pat6_kinds=len(pat)),
          open(os.path.join(HERE, 'r190b.json'), 'w'), indent=1, ensure_ascii=False)
print('\n断言 %d 条，FAIL %d 条' % (N, len(fails)))
sys.exit(1 if fails else 0)
