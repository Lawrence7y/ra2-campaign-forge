#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 m10（定稿三）：把 R204 全部结论固化为可复算判据，并订正 m8 的两条。
m8 自错：① Z2c「段边界 mdisp 不减」实测 33 升 / 3 降 / 652 平，断言方向错；② Z3d 属性 1 与 5 在 mdisp 重复上都是 100%，该量无区分力。
"""
import sys, struct, collections, json, statistics, random
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
def in_text(x): return x is not None and LO <= x < HI
COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=s32(w[i+1]), ptd=w[i+3], pchd=w[i+4], name=nm.decode('latin1'))
VTI = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VTI[base + 4 * i] = P.dw(base + 4 * i - 4)
G = collections.defaultdict(list)
for c, v in COL.items(): G[v['pchd']].append(c)
CHD = sorted(G)
BCD = {a: [P.dw(P.dw(a + 12) + 4 * j) for j in range(P.dw(a + 8))] for a in CHD}
uniq = sorted(set(b for v in BCD.values() for b in v))
ATTR = {a: P.dw(a + 4) for a in CHD}
mi = {a: any(s32(P.dw(b+8)) != 0 for b in BCD[a]) for a in CHD}
mv = {a: len(G[a]) > 1 for a in CHD}
g1 = [a for a in CHD if ATTR[a] == 1]; g5 = [a for a in CHD if ATTR[a] == 5]

# ---- W1 属性 1 vs 5 的真正区分量（穷举 8 个候选） ----
def probes(a):
    v = BCD[a]
    ms = [s32(P.dw(b+8)) for b in v]
    nseg = 1 + sum(1 for i in range(len(v)-1) if v[i+1]-v[i] != -24)
    return dict(
        n=len(v), nseg=nseg, views=len(G[a]),
        md_dup=len(ms) != len(set(ms)),
        md_zero=ms.count(0),
        md_nonzero=len([x for x in ms if x != 0]),
        last_md=ms[-1],
        ns_view_ratio=len(v) / max(1, len(G[a])),
        total_slots=sum(sum(1 for k in range(0, 4000) if False) for _ in G[a]),
        shared_bcd=sum(1 for b in v if sum(1 for x in BCD.values() if b in x) > 1),
    )
p1 = [probes(a) for a in g1]; p5 = [probes(a) for a in g5]
rows = []
for k in ('n', 'nseg', 'views', 'md_zero', 'md_nonzero', 'last_md', 'shared_bcd'):
    try:
        m1v = statistics.mean([p[k] for p in p1]); m5v = statistics.mean([p[k] for p in p5])
    except Exception:
        m1v = m5v = None
    rows.append((k, m1v, m5v, (m5v - m1v) if m1v is not None else None))
print('   W1 属性 1(%d) vs 5(%d) 的 7 个候选量：' % (len(g1), len(g5)))
for k, x, y, d in rows:
    print('      %-12s 1:%-8.3f 5:%-8.3f 差:%.3f' % (k, x, y, d))
ck('W1a 存在区分量（|差| > 10%）', any(abs(d) > 0.1 * max(1e-9, abs(x)) for k, x, y, d in rows if x is not None),
   [(k, round(d, 3)) for k, x, y, d in rows])
# views 分布本身
v1 = collections.Counter(len(G[a]) for a in g1); v5 = collections.Counter(len(G[a]) for a in g5)
print('   W1 视图数分布 1:%s  5:%s' % (dict(v1), dict(v5)))
ck('W1b 属性 1 含 5 个单视图 MI 类（唯一集差）', v1.get(1, 0) == 5, v1.get(1, 0))
ck('W1c 属性 5 无单视图', v5.get(1, 0) == 0, v5.get(1, 0))

# ---- W2 段边界 mdisp 三种走向的正确表述 ----
up = down = same = 0; downs = []
for a in CHD:
    v = BCD[a]
    for i in range(len(v)-1):
        if v[i+1] - v[i] != -24:
            d = s32(P.dw(v[i+1]+8)) - s32(P.dw(v[i]+8))
            if d > 0: up += 1
            elif d < 0: down += 1; downs.append((COL[G[a][0]]['name'][:34], hex(v[i]), hex(v[i+1]), d))
            else: same += 1
print('   W2 段边界 mdisp：升 %d / 降 %d / 平 %d' % (up, down, same))
print('   W2 降的 3 例 %s' % downs)
ck('W2a 段边界的绝大多数是「平」（== 0）', same / (up + down + same) > 0.8, same / (up + down + same))
ck('W2b 降的仅 3 例（记录在案）', down == 3, down)

# ---- W3 三条主结论的定稿断言 ----
# 1 名判据 partition == 指针判据 partition
gd = collections.Counter(len(v) for v in G.values())
ck('W3a pCHD 分组 954 且分布 1:860/2:10/3:6/4:76/5:1/7:1',
   dict(gd) == {1: 860, 2: 10, 3: 6, 4: 76, 5: 1, 7: 1}, dict(gd))
ck('W3b 每组类名唯一', all(len(set(COL[c]["name"] for c in v)) == 1 for v in G.values()),
   sum(1 for v in G.values() if len(set(COL[c]['name'] for c in v)) != 1))
# 2 自有 pTD 子集 + 强反控
def ps(a): return set(P.dw(b) for b in BCD[a])
ck('W3c 自有 pTD ⊆ BCA pTD 954/954', sum(1 for a in CHD if set(COL[c]['ptd'] for c in G[a]) <= ps(a)) == 954,
   sum(1 for a in CHD if set(COL[c]['ptd'] for c in G[a]) <= ps(a)))
random.seed(2048)
fake = sum(1 for a in CHD if set(COL[c]['ptd'] for c in G[a]) <= ps(random.choice([x for x in CHD if len(BCD[x]) == len(BCD[a]) and x != a] or [a])))
ck('W3d 反控 0/954', fake == 0, fake)
# 3 属性 bit0 <=> MI
ck('W3e CHD+4 bit0 == 1 <=> 存在 mdisp!=0 的 BCD（双向 954/954）',
   all(((ATTR[a] & 1) == 1) == mi[a] for a in CHD),
   sum(1 for a in CHD if ((ATTR[a] & 1) == 1) != mi[a]))
ck('W3f 属性取值集合 == {0,1,5}（0:855 / 1:66 / 5:33）',
   (collections.Counter(ATTR.values()) == {0: 855, 1: 66, 5: 33}), dict(collections.Counter(ATTR.values())))
# 4 视图 mdisp 集合 == BCA mdisp 集合 于 939/954
eq = sum(1 for a in CHD if set(COL[c]['mdisp'] for c in G[a]) == set(s32(P.dw(b+8)) for b in BCD[a]))
ck('W3g 视图 mdisp 集合 == BCA mdisp 集合 939/954', eq == 939, eq)
ck('W3h 15 例不等时 BCA 只多不少（单一方向）',
   all(set(COL[c]['mdisp'] for c in G[a]) <= set(s32(P.dw(b+8)) for b in BCD[a]) for a in CHD),
   sum(1 for a in CHD if not set(COL[c]['mdisp'] for c in G[a]) <= set(s32(P.dw(b+8)) for b in BCD[a])))
ck('W3i 5 个仅 BCA 侧 MI 类 == ATL 事件 sink', 
   sorted(hex(a) for a in CHD if mi[a] and not mv[a]) == ['0x80e680','0x80e740','0x80e780','0x80e7c0','0x80e998'],
   [hex(a) for a in CHD if mi[a] and not mv[a]])

# ---- W4 BCD 池结构 ----
ck('W4a 1002 个 BCD 全 8 字节对齐，mod 24 三态 {0,8,16}', len(set(u % 24 for u in uniq)) == 3, sorted(collections.Counter(u % 24 for u in uniq).items()))
refc = collections.Counter(b for v in BCD.values() for b in v)
ck('W4b 共享 BCD 304 个、最大引用 98', (sum(1 for v in refc.values() if v > 1), max(refc.values())) == (304, 98),
   (sum(1 for v in refc.values() if v > 1), max(refc.values())))
ck('W4c BCA 组内差分 -24 占 973/1661', collections.Counter(BCD[a][i+1]-BCD[a][i] for a in CHD for i in range(len(BCD[a])-1))[-24] == 973,
   collections.Counter(BCD[a][i+1]-BCD[a][i] for a in CHD for i in range(len(BCD[a])-1))[-24])
# 反控：随机抽样 1002 个 8 对齐地址，看「自有 pTD 子集」判据
random.seed(2049)
rd = P.B['.rdata']
sup = 0
for tri in range(200):
    a = random.choice(CHD); n = len(BCD[a])
    base = rd['lo'] + 8 * random.randrange(0, (rd['rawsize'] - 8) // 8)
    arr = [P.dw(base + 4 * j) for j in range(n)]
    if any(P.where(b) != '.rdata' for b in arr): continue
    if set(COL[c]['ptd'] for c in G[a]) <= set(P.dw(b) for b in arr): sup += 1
ck('W4d 反控：随机 .rdata 数组上判据成立率 < 5%', sup < 10, sup)

json.dump(dict(N=N, fails=fails, attr_cross={str(k): v for k, v in collections.Counter((ATTR[a], mi[a], mv[a]) for a in CHD).items()},
               rows=rows, up=up, down=down, same=same, downs=downs, eq=eq, rand_sup=sup),
          open('/home/t628/projects/ra2-campaign-forge/_r204/m10_final2.json','w'), ensure_ascii=False, indent=1)
print('\n== %d assertions, %d FAIL ==' % (N, len(fails)))
print('FAILS:', fails)
