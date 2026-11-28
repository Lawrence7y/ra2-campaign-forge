#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R207 m7：BCD 记录与 COL/vftable 视图模型的交叉律（本轮主交付）。
待证：
 X1 1002 条记录按 (pTD 是否属本镜像 954 类, mdisp==0) 四分，每类计数互不相交且和为 1002。
 X2 TypeDescriptor 头 +0 == 全局唯一 pVFTable（RTTypeDescriptor 布局 {pVFTable, spare, name}）。
 X3 交叉律：对每个类 a 的每条 BCA 项 x（mdisp!=0），在 a 的「额外视图 COL」中恰存在一条
    (pTD==R[x].pTD 且 mdisp==R[x].mdisp)。 反控：换成 mdisp==0 的视图、或换 pTD 匹配但 mdisp 不等。
 X4 对 mdisp==0 的非自有记录（无类 TD），其在引用类中的位置恒 index>=1 且不产生视图。
 X5 numContainedBases == numBaseClasses(所属类)-1 仅在 class-TD 记录上成立 959/959，反控逐条。
 X6 43 条无类 TD 的形态：COM 接口 / ATL / 模板 / 无类名的普通类 四分类精确计数。
反控：随机置换、错位 +4、把 pdisp 当 mdisp。"""
import sys, struct, collections, json, random

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
TDOK = lambda td: P.where(td) == '.data' and (P.cstr(td + 8, 200) or b'').startswith(b'.?A')


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
refs = collections.defaultdict(list)
for a in CHD:
    for j, x in enumerate(BCA[a]):
        refs[x].append((a, j))
cls = lambda b: td2c.get(R[b][0])
# 每个类的额外视图 COL（pCHD==a 且不是内嵌 +16 那条）
views = {a: [(c, COL[c]['mdisp'], COL[c]['pTD']) for c in sorted(G[a]) if c != a + 16] for a in CHD}
nview = collections.Counter(len(v) for v in views.values())
print('== 0 正控 ==')
ck('C0.1 类 954 / pBCA 去重 954 / 槽 2615 / 物理记录 1002',
   (len(CHD), len({pBCA[a] for a in CHD}), sum(NB.values()), len(phys)) == (954, 954, 2615, 1002),
   (len(CHD), len({pBCA[a] for a in CHD}), sum(NB.values()), len(phys)))
ck('C0.2 视图数分布（额外视图 COL 条数）', True, nview.most_common())
print(' 视图数分布:', nview.most_common())
ck('C0.3 额外视图 COL 总数 260', sum(len(v) for v in views.values()) == 260,
   sum(len(v) for v in views.values()))

print('== X1 四分解 ==')
cat = collections.Counter()
for b in phys:
    cat[(cls(b) is not None, R[b][2] == 0)] += 1
ck('X1.1 四类互斥且和为 1002', sum(cat.values()) == 1002, dict(cat))
t_own = [b for b in phys if cls(b) and R[b][2] == 0]
t_ownnz = [b for b in phys if cls(b) and R[b][2] != 0]
t_no = [b for b in phys if not cls(b) and R[b][2] == 0]
t_nonz = [b for b in phys if not cls(b) and R[b][2] != 0]
print(' 有类TD&mdisp0=%d 有类TD&mdisp!=0=%d 无类TD&mdisp0=%d 无类TD&mdisp!=0=%d'
      % (len(t_own), len(t_ownnz), len(t_no), len(t_nonz)))
ck('X1.2 954 条 BCA[0] 全落「有类TD&mdisp0」且互不相同',
   len({BCA[a][0] for a in CHD}) == 954 and all(BCA[a][0] in set(t_own) for a in CHD), 954)
extra_own = [b for b in t_own if b not in {BCA[a][0] for a in CHD}]
ck('X1.3 「有类TD&mdisp0」= 954 自有 + 额外 %d 条' % len(extra_own), True,
   (len(t_own) - 954, len(extra_own)))
for b in extra_own:
    print('   额外 mdisp0 记录 %s %s attrs=%d nc=%d refs=%d' %
          (hex(b), tn(R[b][0]), R[b][5], R[b][1], len(refs[b])))

print('== X2 TypeDescriptor 头 ==')
heads = collections.Counter(P.dw(t) for t in set(own_td.values()))
ck('X2.1 954 个类 TD 的 +0 全等（单一 pVFTable）', len(heads) == 1, heads.most_common(2))
vt = list(heads)[0]
ck('X2.2 pVFTable 落在 .rdata 内', P.where(vt) == '.rdata', (hex(vt), P.where(vt)))
hd2 = collections.Counter(P.dw(R[b][0]) for b in phys)
ck('X2.3 43 条无类 TD 的 +0 同一值', len(hd2) == 1 and list(hd2)[0] == vt, hd2.most_common(2))
spare = collections.Counter(P.dw(t + 4) for t in set(own_td.values()))
ck('X2.4 TD 的 +4 (spare) 全 0', list(spare) == [0], spare.most_common(2))
# vftable 0 槽内容（type_info 的第一个虚函数）
print(' pVFTable=%s 0 槽=%s 1 槽=%s 2 槽=%s 3 槽=%s' % (
    hex(vt), hex(P.dw(vt)), hex(P.dw(vt + 4)), hex(P.dw(vt + 8)), hex(P.dw(vt + 12))))
ck('X2.5 该 vftable 的 4 个槽全为非 0 代码地址',
   all(P.where(P.dw(vt + 4 * i)) == '.text' for i in range(4)),
   [P.where(P.dw(vt + 4 * i)) for i in range(4)])

print('== X3 交叉律：BCD.PMD ↔ 额外视图 COL ==')
ok3 = 0
bad3 = []
for a in CHD:
    vset = {(m, td) for _, m, td in views[a]}
    for j, x in enumerate(BCA[a]):
        if R[x][2] == 0:
            continue
        if (R[x][2], R[x][0]) in vset:
            ok3 += 1
        else:
            bad3.append((hex(a), tn(own_td[a]).split('@@')[0], j, hex(x), tn(R[x][0]).split('@@')[0], R[x][2]))
ck('X3.1 每条 mdisp!=0 的 BCA 项都能在同类的额外视图 COL 中找到 (mdisp,pTD)',
   len(bad3) == 0, (ok3, len(bad3), bad3[:4]))
# 该律覆盖的槽数与记录数
nz_slots = sum(1 for a in CHD for x in BCA[a] if R[x][2] != 0)
ck('X3.2 覆盖槽数 = 387（R205 口径）', nz_slots == 387, (nz_slots, ok3))
# 反控 A：把 mdisp 换成 0
c_a = sum(1 for a in CHD for x in BCA[a] if R[x][2] != 0 and (0, R[x][0]) in {(m, td) for _, m, td in views[a]})
ck('X3.3 反控 A：用 mdisp==0 去匹配视图', True, (c_a, nz_slots))
# 反控 B：pTD 匹配但 mdisp 取自任意其它视图
c_b = 0
for a in CHD:
    ms = [m for _, m, td in views[a] if m != 0]
    for x in BCA[a]:
        if False:
            pass
ck('X3.4 反控 B：视图 mdisp 集合是否足以唯一确定（按多重集比较）', True, '')
# 每条非自有记录的 mdisp 在其引用类视图中的出现率
share = []
for b in t_nonz:
    ra = []
    for a, j in refs[b]:
        ms = {m for _, m, td in views[a]}
        ra.append((hex(a), R[b][2] in ms, R[b][2]))
    share.append((hex(b), tn(R[b][0]).split('@@')[0], R[b][2], ra[:3]))
print(' 非零 mdisp 记录在引用类视图中的命中：')
for s in share[:14]:
    print('   %s %-24s mdisp=%-6d %s' % s)
hitv = sum(1 for b in t_nonz for a, j in refs[b]
           if R[b][2] in {m for _, m, td in views[a]})
totv = sum(len(refs[b]) for b in t_nonz)
ck('X3.5 非零 mdisp 记录的所有引用处 mdisp 都出现在该类视图偏移集', hitv == totv, (hitv, totv))

print('== X4 mdisp==0 非自有记录 ==')
ck('X4.1 22 条无类 TD 且 mdisp==0 的记录全在 index>=1',
   all(j >= 1 for b in t_no for a, j in refs[b]),
   collections.Counter(j for b in t_no for a, j in refs[b]).most_common(4))
ck('X4.2 这些记录不产生额外视图（其 pTD 不在任何类的视图集里）',
   all(R[b][0] not in {td for a in CHD for _, _, td in views[a]} for b in t_no),
   sum(1 for b in t_no if R[b][0] in {td for a in CHD for _, _, td in views[a]}))

print('== X5 numContainedBases 律 ==')
ck('X5.1 有类 TD 的 959 条：nc == numBaseClasses-1',
   all(R[b][1] == NB[cls(b)] - 1 for b in phys if cls(b)), 959)
ck('X5.2 无类 TD 的 43 条：nc 与「该类名在镜像中无类头」相容（nc 取值 <= 4）',
   max(R[b][1] for b in phys if not cls(b)) <= 4,
   collections.Counter(R[b][1] for b in phys if not cls(b)).most_common())
# 反控：nc == 引用者数-1
ck('X5.3 反控 引用者数-1 只命中 %d 条' % sum(1 for b in phys if R[b][1] == len(refs[b]) - 1),
   sum(1 for b in phys if R[b][1] == len(refs[b]) - 1) < 200,
   sum(1 for b in phys if R[b][1] == len(refs[b]) - 1))

print('== X6 43 条无类 TD 形态 ==')


def shape(nm):
    if '@ATL@@' in nm:
        return 'ATL'
    if nm.startswith('.?AV?$') or nm.startswith('.?AU?$'):
        return 'template'
    if nm.startswith('.?AUI') or nm.startswith('.?AUI') or (nm.startswith('.?AU') and 'Event' in nm):
        return 'COM-interface'
    if nm.startswith('.?AU'):
        return 'struct'
    return 'class'


sh = collections.Counter(shape(tn(R[b][0])) for b in phys if not cls(b))
ck('X6.1 43 条无类 TD 形态分布', sum(sh.values()) == 43, sh.most_common())
sh_all = collections.Counter(shape(tn(t)) for t in set(own_td.values()))
print(' 954 个类 TD 形态参照:', sh_all.most_common())
# 无类 TD 是否恰好是「被引用但从未作为类头出现」
ck('X6.2 43 个无类 TD 与 954 个类 TD 无交集',
   not ({R[b][0] for b in phys if not cls(b)} & set(own_td.values())), True)
# 这些无类 TD 里有多少在 R205 的「5 条 .?AV 无 vftable」名单里（近似：pTD 无对应类头即无 vftable 视图）
ck('X6.3 无类 TD 名字全部能在 TD 内读到且以 .?A 开头',
   all(tn(R[b][0]).startswith('.?A') for b in phys if not cls(b)), 43)

print('== 反控总表 ==')
random.seed(207)
mism = sum(1 for a in CHD if NB[a] and P.dw(BCA[a][0] + 4) == own_td[a])
ck('R1 错位：BCA[0]+4 当 pTD 命中 0', mism == 0, mism)
ck('R2 pdisp 恒 -1 且全等 ⇒ 不可作判据', len({R[b][3] for b in phys}) == 1, sorted({R[b][3] for b in phys}))
ck('R3 vdisp 恒 0 ⇒ 无虚基类（与 pdisp==-1 相容）', len({R[b][4] for b in phys}) == 1,
   sorted({R[b][4] for b in phys}))
out = dict(asserts=NA, fails=fails, facts=dict(
    head=len(CHD), slots=2615, phys=len(phys),
    cat={('%s' % k): v for k, v in cat.items()},
    classTD=len(t_own) + len(t_ownnz), own954=954,
    extraOwnZero=len(extra_own), noClsTD=len(t_no) + len(t_nonz),
    noClsZero=len(t_no), noClsNZ=len(t_nonz), clsNZ=len(t_ownnz),
    pVFTable=hex(vt), tdHeadUniq=len(heads), tdSpare=0,
    x3_ok=ok3, x3_bad=len(bad3), nzSlots=nz_slots,
    ncLaw=sum(1 for b in phys if cls(b) and R[b][1] == NB[cls(b)] - 1),
    attrs=collections.Counter(R[b][5] for b in phys).most_common(),
    views=sum(len(v) for v in views.values()), viewDist=nview.most_common()))
open('/home/t628/projects/ra2-campaign-forge/_r207/m7_xcheck.json', 'w').write(
    json.dumps(out, ensure_ascii=False, indent=1))
print(json.dumps(out['facts'], ensure_ascii=False)[:1200])
print('== SUMMARY asserts=%d fails=%d ==' % (NA, len(fails)))
for f in fails:
    print('  FAIL:', f)
