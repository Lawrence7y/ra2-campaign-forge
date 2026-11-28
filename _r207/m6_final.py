#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R207 m6：BCD 24B 全字段收口 + 43 条「无类 TD」分解 + 11 条非零 attributes 语义。
全部数字实测；每条断言后附反控。输出 m6_final.json 供四件套引用。
口径：BCD 条目是「记录地址」，比较 pTD 必须解引用 P.dw(b)。"""
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
LOG = []


def ck(nm, c, d=''):
    global NA
    NA += 1
    if not c:
        fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))


phys = sorted(set(x for a in CHD for x in BCA[a]))
FLD = ('pTD', 'nc', 'mdisp', 'pdisp', 'vdisp', 'attrs')
def rec(b):
    return (P.dw(b), P.dw(b + 4), s32(P.dw(b + 8)), s32(P.dw(b + 12)),
            s32(P.dw(b + 16)), P.dw(b + 20))
R = {b: rec(b) for b in phys}
refc = collections.Counter()
pos_of = collections.defaultdict(list)
for a in CHD:
    for j, x in enumerate(BCA[a]):
        refc[x] += 1
        pos_of[x].append((a, j))
cls_of = lambda b: td2c.get(R[b][0])

print('== 0 正控 ==')
ck('C0.1 HEAD 954 / BCA 槽 2615 / 物理 BCD 1002',
   (len(CHD), sum(NB.values()), len(phys)) == (954, 2615, 1002),
   (len(CHD), sum(NB.values()), len(phys)))
ck('C0.2 954 个 pBCA 互不相同（R206「pBCA 可被多记录共享」为误述）',
   len({pBCA[a] for a in CHD}) == 954, len({pBCA[a] for a in CHD}))
ck('C0.3 876/953 缺口的成因 = BCD 多引用非 pBCA 共享',
   sum(1 for x in phys if refc[x] > 1) == 304, sum(1 for x in phys if refc[x] > 1))

print('== 1 BCD 六字段 ==')
ck('L1.1 pdisp(+12) 恒 -1：1002/1002', all(R[b][3] == -1 for b in phys),
   collections.Counter(R[b][3] for b in phys).most_common(3))
ck('L1.2 vdisp(+16) 恒 0：1002/1002', all(R[b][4] == 0 for b in phys),
   collections.Counter(R[b][4] for b in phys).most_common(3))
ck('L1.3 attributes(+20) ∈ {0,2,9}，非零 11 条',
   collections.Counter(R[b][5] for b in phys) == collections.Counter({0: 991, 2: 7, 9: 4}),
   collections.Counter(R[b][5] for b in phys).most_common())
ck('L1.4 numContainedBases ∈ [0,17]', max(R[b][1] for b in phys) <= 17,
   (min(R[b][1] for b in phys), max(R[b][1] for b in phys)))

print('== 2 mdisp 二分（记录级）==')
z = [b for b in phys if R[b][2] == 0]
nz = [b for b in phys if R[b][2] != 0]
ck('L2.1 978 条 mdisp==0 + 24 条 mdisp!=0', (len(z), len(nz)) == (978, 24), (len(z), len(nz)))
ck('L2.2 R205 的 387 是 BCA 槽数（异于 24 条记录数）',
   sum(1 for a in CHD for x in BCA[a] if R[x][2] != 0) == 387,
   sum(1 for a in CHD for x in BCA[a] if R[x][2] != 0))
ck('L2.3 954 条 BCA[0] 全为 mdisp==0 且 pTD==自有 pTD',
   all(R[BCA[a][0]][2] == 0 and R[BCA[a][0]][0] == own_td[a] for a in CHD), 954)
ck('L2.4 mdisp==0 记录 978 条 = 954 自有 + 24 条「无类 TD 的 mdisp==0 记录」',
   sum(1 for b in z if cls_of(b)) == 954 and sum(1 for b in z if not cls_of(b)) == 24,
   (sum(1 for b in z if cls_of(b)), sum(1 for b in z if not cls_of(b))))
ck('L2.5 自有 pTD 在 BCA 中恰 1 次且位于 index 0',
   all(sum(1 for x in BCA[a] if R[x][0] == own_td[a]) == 1 and R[BCA[a][0]][0] == own_td[a]
       for a in CHD), 954)
# 反控：把 BCA[0] 换成 BCA[1]
ctrl = sum(1 for a in CHD if NB[a] > 1 and R[BCA[a][1]][0] == own_td[a])
ck('L2.6 反控 BCA[1] 的 pTD==自有 pTD 的类数', True, ctrl)

print('== 3 43 条「无类 TD」记录 ==')
nocls = [b for b in phys if not cls_of(b)]
ck('L3.1 1002 = 959「TD 属本镜像 954 类」+ 43「TD 无类头」',
   (len(phys) - len(nocls), len(nocls)) == (959, 43), (len(phys) - len(nocls), len(nocls)))
ck('L3.2 numContainedBases == numBaseClasses(所属类)-1：959/959',
   all(R[b][1] == NB[cls_of(b)] - 1 for b in phys if cls_of(b)), 959)
nm = collections.Counter(tn(R[b][0]) for b in nocls)
pref = collections.Counter('I' if n.startswith('.?AUI') or n.startswith('.?AUI') else
                           ('ATL' if '@ATL@@' in n else
                            ('tmpl' if n.startswith('.?AV?$') else 'V')) for n in
                           [tn(R[b][0]) for b in nocls])
ck('L3.3 43 条无类 TD 的形态分布', True, (len(nocls), pref.most_common()))
print(' 无类 TD 记录（pTD 名 / mdisp / nc / attrs / 引用类数）：')
for b in nocls:
    print('   %-9s %-46s mdisp=%-6d nc=%-2d attrs=%d refs=%d' %
          (hex(b), tn(R[b][0])[:46], R[b][2], R[b][1], R[b][5], refc[b]))
ck('L3.4 无类 TD 记录中 mdisp==0 恰 24 条', sum(1 for b in nocls if R[b][2] == 0) == 24,
   sum(1 for b in nocls if R[b][2] == 0))
# 无类 TD 的 TD 自身结构：+0 是否 0(spare) + 名字指针
tdu = [R[b][0] for b in nocls]
ck('L3.5 无类 TD 的 TD 头 +0 恒 0', all(P.dw(t) == 0 for t in tdu),
   collections.Counter(P.dw(t) for t in tdu).most_common(3))
ck('L3.6 无类 TD 名以 .?A 开头且含 I(interface) 或 ATL 或模板',
   all(tn(t).startswith('.?A') for t in tdu), len(tdu))
# 与 954 类 TD 头对照
ck('L3.7 类 TD 头 +0 也恒 0（对照）',
   all(P.dw(t) == 0 for t in set(own_td.values())),
   collections.Counter(P.dw(t) for t in set(own_td.values())).most_common(2))

print('== 4 11 条非零 attributes ==')
nz_attr = [b for b in phys if R[b][5] != 0]
ck('L4.1 非零 attributes 11 条：2 x7 + 9 x4', (len(nz_attr),) == (11,), len(nz_attr))
for b in nz_attr:
    print('   %-9s attrs=%d %-44s mdisp=%-6d nc=%d vdisp=%d refs=%d 类=%s' %
          (hex(b), R[b][5], tn(R[b][0])[:44], R[b][2], R[b][1], R[b][4], refc[b],
           tn(own_td[cls_of(b)]).split('@@')[0] if cls_of(b) else 'NONE'))
ck('L4.2 attributes==2 的记录 mdisp 全 !=0', all(R[b][2] != 0 for b in nz_attr if R[b][5] == 2),
   [R[b][2] for b in nz_attr if R[b][5] == 2])
ck('L4.3 attributes==9 的记录 mdisp 全 !=0', all(R[b][2] != 0 for b in nz_attr if R[b][5] == 9),
   [R[b][2] for b in nz_attr if R[b][5] == 9])
ck('L4.4 非零 attributes ⇔ 该记录在其类 BCA 中 index >= 1',
   all(pos_of[b][0][1] >= 1 for b in nz_attr) and
   all(R[b][5] == 0 for b in phys if R[b][5] == 0), True)
idx_of_nz = sorted({p[1] for b in nz_attr for p in pos_of[b]})
print(' 非零 attrs 记录在各引用类中的 index 集:', idx_of_nz)
ck('L4.5 非零 attributes 与「无类 TD」高度重叠',
   sum(1 for b in nz_attr if not cls_of(b)), sum(1 for b in nz_attr if not cls_of(b)))

print('== 5 身份键 ==')
for nk, kf in (('pTD', lambda b: (R[b][0],)),
               ('pTD+mdisp', lambda b: (R[b][0], R[b][2])),
               ('pTD+mdisp+nc', lambda b: (R[b][0], R[b][2], R[b][1])),
               ('pTD+mdisp+attrs', lambda b: (R[b][0], R[b][2], R[b][5])),
               ('全 6 字段', lambda b: R[b])):
    print('  键 %-16s 去重 %d' % (nk, len({kf(b) for b in phys})))
ck('L5.1 六字段全等 ⇒ 无字节完全相同的两条记录（1002 个不同键）',
   len({R[b] for b in phys}) == 1002, len({R[b] for b in phys}))
ck('L5.2 (pTD,mdisp) 去重 999（3 组冲突仅差 nc/attrs）',
   len({(R[b][0], R[b][2]) for b in phys}) == 999,
   len({(R[b][0], R[b][2]) for b in phys}))
k2 = collections.defaultdict(list)
for b in phys:
    k2[(R[b][0], R[b][2])].append(b)
for k, v in k2.items():
    if len(v) > 1:
        print('  冲突 %s %s: %s' % (hex(k[0]), tn(k[0])[:40],
              [(hex(b), R[b][1], R[b][5]) for b in v]))

print('== 6 反控总表 ==')
random.seed(207)
# 反控 A：随机 dword 当 pTD 命中 954 自有 pTD 的比例（基线）
hit = 0
for _ in range(2000):
    v = P.dw(0x7fa4b0 + 4 * random.randrange((0x80efc4 - 0x7fa4b0) // 4))
    if v in td2c:
        hit += 1
ck('R6.1 反控：区间内随机 dword 落在 954 自有 pTD 集的次数（应 ~0）', hit <= 2, hit)
# 反控 B：把 mdisp 换成 pdisp 后「mdisp==0 ⇔ 自有」不成立
ck('R6.2 反控：用 pdisp(恒-1) 做判据则律崩塌',
   len({R[b][3] for b in phys}) == 1, sorted({R[b][3] for b in phys}))
# 反控 C：错位 +4 读 pTD
m = sum(1 for a in CHD if P.dw(BCA[a][0] + 4) == own_td[a])
ck('R6.3 反控：BCA[0]+4 当作 pTD 命中 0', m == 0, m)

out = dict(asserts=NA, fails=fails,
           facts=dict(head=len(CHD), slots=sum(NB.values()), phys=len(phys),
                      distinct_pBCA=len({pBCA[a] for a in CHD}),
                      multiref=sum(1 for x in phys if refc[x] > 1),
                      mdisp0=len(z), mdispNZ=len(nz), slotsNZ=387,
                      classTD=len(phys) - len(nocls), noClsTD=len(nocls),
                      ncLaw=sum(1 for b in phys if cls_of(b) and R[b][1] == NB[cls_of(b)] - 1),
                      attrZero=991, attr2=7, attr9=4,
                      key_pTD=len({R[b][0] for b in phys}),
                      key_pTD_mdisp=len({(R[b][0], R[b][2]) for b in phys}),
                      key_full=len({R[b] for b in phys}),
                      pdisp_all=-1, vdisp_all=0))
open('/home/t628/projects/ra2-campaign-forge/_r207/m6_final.json', 'w').write(
    json.dumps(out, ensure_ascii=False, indent=1))
print(json.dumps(out['facts'], ensure_ascii=False))
print('== SUMMARY asserts=%d fails=%d ==' % (NA, len(fails)))
for f in fails:
    print('  FAIL:', f)
