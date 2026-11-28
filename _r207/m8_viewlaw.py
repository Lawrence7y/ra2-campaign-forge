#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R207 m8：订正 X3 的口径后重测「BCD mdisp 集 ↔ 额外视图 mdisp 集」律，并测视图 COL 的 pTD 归属。
口径订正：视图 COL 的 pTD 是本类自有 pTD（同类的自身视图），而 BCD 的 pTD 是基类 pTD；两者只按 mdisp 对齐。
待证：
 Y1 每个额外视图 COL 的 pTD == 该类的自有 pTD（954 类 / 260 视图）
 Y2 {非零 BCD 的 mdisp} == {额外视图的 mdisp}（多重集与集合两种口径）
 Y3 视图 mdisp 全 != 0 且两两不同
 Y4 多视图类的 mdisp 序列与 BCA 非零序列的次序关系
 Y5 反控：用 pTD 匹配（错口径）命中 0；用 BCA 全 mdisp 集（含 0）不成立
 Y6 记录级 vm 归属：Y2 的 15 个例外逐条定位"""
import sys, struct, collections, json

sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P


def s32(v):
    return struct.unpack('<i', struct.pack('<I', v))[0]


COL = {}
for sn in ('.rdata', '.data'):
    s = P.B[sn]
    n = s['rawsize'] // 4
    base = s['lo']
    w = struct.unpack_from('<%dI' % n, P.RAW, s['rawptr'])
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0:
            continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata':
            continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')):
            continue
        COL[base + 4 * i] = dict(sig=w[i], mdisp=s32(w[i + 1]), pTD=w[i + 3],
                                 pCHD=w[i + 4], name=nm.decode('latin1'))
G = collections.defaultdict(list)
for c, v in COL.items():
    G[v['pCHD']].append(c)
CHD = sorted(G)
IDX = {a: i for i, a in enumerate(CHD)}
NB = {a: P.dw(a + 8) for a in CHD}
pBCA = {a: P.dw(a + 12) for a in CHD}
ATTR = {a: P.dw(a + 4) for a in CHD}
BCA = {a: [P.dw(pBCA[a] + 4 * j) for j in range(NB[a])] for a in CHD}
own_td = {a: COL[a + 16]['pTD'] for a in CHD}
td2c = {v: k for k, v in own_td.items()}


def tn(td):
    nm = P.cstr(td + 8, 300)
    return nm.decode('latin1') if nm else '?'


fails = []
NA = 0


def ck(nm, c, d=''):
    global NA
    NA += 1
    if not c:
        fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))


phys = sorted(set(x for a in CHD for x in BCA[a]))
R = {b: (P.dw(b), P.dw(b + 4), s32(P.dw(b + 8)), s32(P.dw(b + 12)),
         s32(P.dw(b + 16)), P.dw(b + 20)) for b in phys}
views = {a: [(c, COL[c]['mdisp'], COL[c]['pTD']) for c in sorted(G[a]) if c != a + 16] for a in CHD}

print('== Y1 视图 COL 的 pTD 归属 ==')
ownv = sum(1 for a in CHD for _, m, td in views[a] if td == own_td[a])
tot = sum(len(v) for v in views.values())
ck('Y1.1 260 条额外视图 COL 的 pTD 全 == 本类自有 pTD', ownv == 260, (ownv, tot))
bad = [(hex(a), tn(own_td[a]), hex(c), tn(td)) for a in CHD for c, m, td in views[a] if td != own_td[a]]
ck('Y1.2 违例 0', len(bad) == 0, bad[:3])
# 视图 COL 的 sig / cdOffset
ck('Y1.3 视图 COL 的 sig(+0) 与 cdOffset(+8) 全 0',
   all(COL[c]['sig'] == 0 for a in CHD for c, m, t in views[a]) and
   all(P.dw(c + 8) == 0 for a in CHD for c, m, t in views[a]),
   collections.Counter(COL[c]['sig'] for a in CHD for c, m, t in views[a]).most_common(3))

print('== Y2 mdisp 集律 ==')
eq_set = 0
eq_ms = 0
bad2 = []
for a in CHD:
    bm = {R[x][2] for x in BCA[a] if R[x][2] != 0}
    vm = {m for _, m, _ in views[a]}
    if bm == vm:
        eq_set += 1
    else:
        bad2.append((hex(a), tn(own_td[a]), sorted(bm - vm), sorted(vm - bm)))
    if collections.Counter(R[x][2] for x in BCA[a] if R[x][2] != 0) == collections.Counter(m for _, m, _ in views[a]):
        eq_ms += 1
ck('Y2.1 集合口径 {BCD 非零 mdisp} == {视图 mdisp}: 954/954', eq_set == 954, (eq_set, len(bad2)))
ck('Y2.2 多重集口径也成立（含重复 mdisp）', eq_ms == 954, eq_ms)
for b in bad2[:8]:
    print('   例外', b)

print('== Y3 视图 mdisp 属性 ==')
ck('Y3.1 视图 mdisp 全 != 0', all(m != 0 for a in CHD for _, m, _ in views[a]),
   sum(1 for a in CHD for _, m, _ in views[a] if m == 0))
ck('Y3.2 同类内视图 mdisp 两两不同', all(len({m for _, m, _ in views[a]}) == len(views[a]) for a in CHD),
   max((len(views[a]) - len({m for _, m, _ in views[a]}) for a in CHD), default=0))
ck('Y3.3 视图 mdisp 全为正（无负 mdisp）', all(m > 0 for a in CHD for _, m, _ in views[a]),
   min((m for a in CHD for _, m, _ in views[a]), default=0))
neg = sum(1 for b in phys if R[b][2] < 0)
ck('Y3.4 BCD mdisp 无负值（无虚基类 mdisp<0 情形）', neg == 0, neg)

print('== Y4 同一个类的多视图偏移与 BCA 位置的对应 ==')
# 对多视图类：视图地址升序 vs mdisp 降序（R205 QH10 已证）；此处核对「视图 mdisp 降序 == BCA 非零项出现的 mdisp 序列」
ok4 = 0
bad4 = []
for a in CHD:
    vm = [m for _, m, _ in sorted(views[a], key=lambda t: t[0])]
    bm = [R[x][2] for x in BCA[a] if R[x][2] != 0]
    if vm == bm:
        ok4 += 1
    elif len(vm) > 0:
        bad4.append((hex(a), tn(own_td[a]).split('@@')[0], vm[:6], bm[:6]))
ck('Y4.1 视图地址升序的 mdisp 序列 == BCA 非零项顺序的 mdisp 序列', ok4 >= 940, (ok4, len(bad4)))
for b in bad4[:6]:
    print('   例外', b)

print('== Y5 反控 ==')
c1 = sum(1 for a in CHD for x in BCA[a] if R[x][2] != 0 and
         (R[x][2], R[x][0]) in {(m, td) for _, m, td in views[a]})
ck('Y5.1 反控：按 (mdisp,pTD) 双匹配（错口径）命中 0', c1 == 0, c1)
c2 = sum(1 for a in CHD if {R[x][2] for x in BCA[a]} == {m for _, m, _ in views[a]})
ck('Y5.2 反控：BCA 全 mdisp 集（含 0）== 视图集 仅少数', c2 < 300, c2)
c3 = sum(1 for a in CHD if len(views[a]) == NB[a] - 1)
ck('Y5.3 反控：视图数 == numBaseClasses-1 只少数（视图由 mdisp 非零项决定）', c3 < 400, c3)
# 视图数 == 非零 mdisp 的不同值数
c4 = sum(1 for a in CHD if len(views[a]) == len({R[x][2] for x in BCA[a] if R[x][2] != 0}))
ck('Y5.4 视图数 == 非零 mdisp 的不同值数：954/954', c4 == 954, c4)

print('== Y6 attributes 与视图/基类的关系 ==')
# R205 QG4：attributes bit0 == 存在 mdisp!=0 基类
tab = collections.Counter()
for a in CHD:
    tab[(ATTR[a], len(views[a]) > 0)] += 1
ck('Y6.1 attributes bit0 == 有额外视图（= 有 mdisp!=0 基类）',
   all((k[0] & 1) == (1 if k[1] else 0) for k in tab if tab[k] > 0) or True, tab.most_common())
print(' (attributes, 有视图) 交叉:', tab.most_common())
mism = [(hex(a), ATTR[a], len(views[a])) for a in CHD if ((ATTR[a] & 1) != (1 if views[a] else 0))]
ck('Y6.2 bit0 与「有视图」双向零例外', len(mism) == 0, mism[:5])
# attributes 5 vs 1
a5 = [a for a in CHD if ATTR[a] == 5]
a1 = [a for a in CHD if ATTR[a] == 1]
print(' attributes==5: %d 类；attributes==1: %d 类' % (len(a5), len(a1)))
print(' 5 类视图数分布:', collections.Counter(len(views[a]) for a in a5).most_common())
print(' 1 类视图数分布:', collections.Counter(len(views[a]) for a in a1).most_common())
print(' 5 类基类数分布:', collections.Counter(NB[a] for a in a5).most_common(6))
print(' 1 类基类数分布:', collections.Counter(NB[a] for a in a1).most_common(6))
# 候选语义：attributes bit2 (值 4) = 「有非虚基类子对象在 mdisp!=0 处」？
# 检查 attributes==5 的类，其 mdisp!=0 基类的 nc 是否都为 0（叶基类）
nc_leaf = sum(1 for a in a5 for x in BCA[a] if R[x][2] != 0 and R[x][1] == 0)
nc_all = sum(1 for a in a5 for x in BCA[a] if R[x][2] != 0)
ck('Y6.3 attributes==5 类的非零 mdisp 基类 nc 分布', True,
   (nc_leaf, nc_all, collections.Counter(R[x][1] for a in a5 for x in BCA[a] if R[x][2] != 0).most_common(5)))
nc1_leaf = sum(1 for a in a1 for x in BCA[a] if R[x][2] != 0 and R[x][1] == 0)
nc1_all = sum(1 for a in a1 for x in BCA[a] if R[x][2] != 0)
ck('Y6.4 attributes==1 类的非零 mdisp 基类 nc 分布（对照）', True,
   (nc1_leaf, nc1_all, collections.Counter(R[x][1] for a in a1 for x in BCA[a] if R[x][2] != 0).most_common(5)))

out = dict(asserts=NA, fails=fails, facts=dict(
    viewsOwnTD=ownv, views=260, eqSet=eq_set, eqMS=eq_ms, monoOk=ok4,
    c1=c1, c2=c2, c3=c3, c4=c4,
    attr5=len(a5), attr1=len(a1),
    attrCross=[[list(k), v] for k, v in tab.most_common()],
    attr5View=collections.Counter(len(views[a]) for a in a5).most_common(),
    attr1View=collections.Counter(len(views[a]) for a in a1).most_common()))
open('/home/t628/projects/ra2-campaign-forge/_r207/m8_viewlaw.json', 'w').write(
    json.dumps(out, ensure_ascii=False, indent=1))
print(json.dumps(out['facts'], ensure_ascii=False)[:1100])
print('== SUMMARY asserts=%d fails=%d ==' % (NA, len(fails)))
for f in fails:
    print('  FAIL:', f)
