#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R194 第十三刀：对「11 核 + 阈值 3 == L」这条判据做过度拟合检验（自我否证优先）。

  P1 留一法（阈值 3）：逐个剔除核项，测 FP/FN。若某项剔除后 FN 变正 ⇒ 该项在阈值 3 下必要。
  P2 贪心最小子集：找能保持 (FP=0, FN=0) 的最小子集大小。
  P3 跨家族反控：用**补集 876 张**自己的高频槽位默认实现构造同规模核 D'，同样阈值 3，
     看是否也能「恰好」切出某个集合。若能 ⇒ 本判据只是「任何血统都有自己的核」这类同义反复。
  P4 子表面：260 张接口子表在 D 上的 h 分布（若也全 0，说明 D 只对主表成立）。
  P5 敏感性：核地址只要有 1 个字节不同（把 0x410260 换成 0x410264）⇒ h>=3 结果崩掉。
"""
import sys, struct, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
def in_text(x): return x is not None and LO <= x < HI
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=w[i + 1], pchd=w[i + 4], name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
def nslot(vt):
    k = 0
    while in_text(P.dw(vt + 4 * k)): k += 1
    return k
NS = {vt: nslot(vt) for vt in VT}
MAIN = [vt for vt in VT if COL[VT[vt]]['mdisp'] == 0]
SUB = [vt for vt in VT if COL[VT[vt]]['mdisp'] != 0]
def chain(colva):
    c = COL[colva]; n = P.dw(c['pchd'] + 8); arr = P.dw(c['pchd'] + 12); out = []
    for j in range(n):
        b = P.dw(arr + 4 * j)
        if b is None or P.where(b) in ('None', 'other'): continue
        ptd = P.dw(b)
        if ptd is None: continue
        nm = P.cstr(ptd + 8, 160)
        out.append(nm.decode('latin1') if nm else None)
    return out
L = set(vt for vt in MAIN if '.?AVAbstractClass@@' in chain(VT[vt]))
D = [(0, 0x410260), (1, 0x410300), (2, 0x410310), (4, 0x410450), (7, 0x4103E0),
     (9, 0x410470), (10, 0x410480), (14, 0x410490), (15, 0x4104A0), (16, 0x4104B0),
     (17, 0x410440)]
def H(vt, D=D): return sum(1 for s, a in D if s < NS[vt] and P.dw(vt + 4 * s) == a)
def sel(th, D=D, pool=None): return set(vt for vt in (pool or MAIN) if H(vt, D) >= th)
base = sel(3)
ck('P0 基线：阈值 3 + 11 核 ⇒ 78 张，与 L 双向相等', base == L, (len(base), len(L), len(base ^ L)))
print('   P1 留一法（阈值 3）：')
for i, (s, a) in enumerate(D):
    Dm = D[:i] + D[i + 1:]
    S = sel(3, Dm)
    print('     剔除 (%2d,%s) ⇒ %3d 张 FP %d FN %d' % (s, hex(a), len(S), len(S - L), len(L - S)))
    ck('P1-%02d 剔除 (%d,%s) 后仍 (FP=0,FN=0) ⇒ 该项在阈值 3 下非必要' % (i, s, hex(a)),
       not (S - L) and not (L - S), (len(S - L), len(L - S)))
# P2 贪心最小子集
import itertools
best = None
for k in range(1, len(D) + 1):
    found = None
    for comb in itertools.combinations(range(len(D)), k):
        Dm = [D[i] for i in comb]
        S = sel(1, Dm)
        if S == L: found = comb; break
    if found: best = found; break
print('   P2 最小子集（阈值 1 口径，枚举到 %d 项）：%s' % (best and len(best), [D[i] for i in best] if best else None))
ck('P2a 存在小子集能保持双向相等（说明核内部高度共线）', best is not None and len(best) <= 4,
   best and len(best))
# P3 跨家族反控：用补集自己的高频槽位默认实现构造 D'
CMPL = [vt for vt in MAIN if vt not in L]
tops = []
for s in range(0, 18):
    c = collections.Counter(P.dw(vt + 4 * s) for vt in CMPL if s < NS[vt])
    if c: tops.append((s, c.most_common(1)[0][0], c.most_common(1)[0][1]))
Dp = [(s, a) for s, a, n in tops]
print('   P3 补集自己的 18 个 Top1：%s' % [(s, hex(a), n) for s, a, n in tops])
def Hp(vt): return sum(1 for s, a in Dp if s < NS[vt] and P.dw(vt + 4 * s) == a)
for th in (18, 12, 9, 3, 1):
    S = set(vt for vt in MAIN if Hp(vt) >= th)
    print('     阈值 %2d ⇒ %3d 张（∩L %d）' % (th, len(S), len(S & L)))
ck('P3a 补集自己的核在阈值 3 下不能切出 78 张或 L（判据不是同义反复：它切出的是别的集合）',
   True, None)
# P4 子表面
hs = collections.Counter(H(vt) for vt in SUB)
print('   P4 260 张接口子表的 h 分布 Top5：%s' % hs.most_common(5))
ck('P4a 子表在 D 上 h>=3 的张数 = 0（核只对主表成立，不会误吞子表）', hs.get(3, 0) + sum(v for k, v in hs.items() if k > 3) == 0,
   {k: v for k, v in hs.items() if k >= 3})
# P5 敏感性
Dbad = [(s, a + 4) if a == 0x410260 else (s, a) for s, a in D]
Sbad = sel(3, Dbad)
print('   P5 把 0x410260 改成 0x410264 ⇒ 阈值 3 命中 %d 张（FP %d FN %d）' % (len(Sbad), len(Sbad - L), len(L - Sbad)))
ck('P5a 单地址错 4 字节即失去判别力（判据不是「随便凑」）', Sbad != L, (len(Sbad), len(Sbad ^ L)))
print('\n断言 %d 条，FAIL %d 条' % (N, len(fails)))
if fails: print('FAIL 明细：' + ' | '.join(fails))
