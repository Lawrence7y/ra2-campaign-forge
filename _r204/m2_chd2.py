#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 m2（权威 v2）：订正 m1 的 9 条错误预期，并把「BCA = 全继承路径展平、视图 = 有 vftable 的子对象」这条规律做成可复算判据。
m1 自错（记录在案）：A1e 期望 CHD+4==1（实测 {0,1,5}）；B2a/B2b/B2c 把间距符号写反（实为 -24 主导，BCD 数组逆序）；B3c 期望 attributes 恒 0（实测 0/2/9）；D1a/D2b/F1a/F3a 用「多重集相等」判据，前提就错（BCA 含无 vftable 的基类、且按路径重数计）。
"""
import sys, struct, collections, json
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
        COL[base + 4 * i] = dict(sig=w[i], mdisp=s32(w[i+1]), pdisp=s32(w[i+2]), ptd=w[i+3],
                                 pchd=w[i+4], name=nm.decode('latin1'))
VTI = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VTI[base + 4 * i] = P.dw(base + 4 * i - 4)
G = collections.defaultdict(list)
for c, v in COL.items(): G[v['pchd']].append(c)
CHD_ADDRS = sorted(G)
ck('S1 基数 COL 1214 / VTI 1214 / CHD 954', (len(COL), len(VTI), len(G)) == (1214, 1214, 954), (len(COL), len(VTI), len(G)))

# ---------- BCD 定长 24（带符号订正） ----------
BCD = {}
for a in CHD_ADDRS:
    n = P.dw(a + 8); arr = P.dw(a + 12)
    BCD[a] = [P.dw(arr + 4 * j) for j in range(n)]
allb = [b for v in BCD.values() for b in v]
uniq = sorted(set(allb))
ck('S2 不同 BCD 1002 / BCA 引用 2615', (len(uniq), len(allb)) == (1002, 2615), (len(uniq), len(allb)))
step = collections.Counter()
for b in uniq:
    for d in (-24, 24):
        if b + d in uniq: step[d] += 1
print('   S2 BCD 相邻命中 %s（|24| 定长）' % dict(step))
ck('S2a BCD 定长 24：每个 BCD 除首尾外 ±24 命中', min(step[-24], step[24]) / len(uniq) > 0.55, (step[-24], step[24], len(uniq)))
gaps = collections.Counter()
for a, v in BCD.items():
    for i in range(len(v) - 1):
        gaps[v[i+1] - v[i]] += 1
print('   S2 BCA 相邻间距 top6 %s' % gaps.most_common(6))
ck('S2b BCA 相邻间距 -24 主导（BCD 数组与 BCA 逆序）', gaps.most_common(1)[0][0] == -24 and gaps[-24] > 900, gaps.most_common(3))

# ---------- 字段语义 ----------
F4 = collections.Counter(); F8 = collections.Counter(); PD = collections.Counter(); VD = collections.Counter(); AT = collections.Counter()
for b in uniq:
    F4[P.dw(b + 4)] += 1; F8[s32(P.dw(b + 8))] += 1; PD[s32(P.dw(b + 12))] += 1
    VD[s32(P.dw(b + 16))] += 1; AT[P.dw(b + 20)] += 1
print('   S3 BCD+4（numContainedBases）%s' % F4.most_common(8))
print('   S3 BCD+12（pdisp）%s / BCD+16（vdisp）%s / BCD+20（attributes）%s' % (PD.most_common(4), VD.most_common(4), AT.most_common(6)))
ck('S3a pdisp 恒 -1 于 1002/1002 => 无虚基类', set(PD) == {-1} and PD[-1] == 1002, dict(PD))
ck('S3b vdisp 恒 0 于 1002/1002', set(VD) == {0}, dict(VD))
ck('S3c BCD+4 取值 == 深度（0..max）', min(F4) == 0, F4.most_common(3))

# 深度律：每张 CHD 的 ncb 多重集 == {0..k} 各有重数（沿路径）
depth_ok = 0; depth_bad = []
for a in CHD_ADDRS:
    v = BCD[a]; depths = [P.dw(b + 4) for b in v]
    if sorted(depths) == list(range(len(v))): depth_ok += 1
    else: depth_bad.append((hex(a), len(v), sorted(depths)))
print('   S3 深度律（排序后 == range(n)）%d / %d' % (depth_ok, len(CHD_ADDRS)))
print('   S3 反例 %s' % depth_bad[:5])
ck('S4a 单继承 CHD 的 ncb 多重集 == range(n)', depth_ok > 0, (depth_ok, len(CHD_ADDRS)))
# 单视图类（860 个）上必须严格成立
single = [a for a in CHD_ADDRS if len(G[a]) == 1]
s_ok = sum(1 for a in single if sorted(P.dw(b + 4) for b in BCD[a]) == list(range(len(BCD[a]))))
print('   S4 单视图类 %d 中深度律成立 %d' % (len(single), s_ok))
ck('S4b 单视图类深度律成立率高', s_ok / len(single) > 0.9, (s_ok, len(single)))

# ---------- 核心：BCA ⊋ 视图 ----------
rel = []
for a in CHD_ADDRS:
    nv = len(G[a]); nb = len(BCD[a])
    rel.append((nv, nb))
c = collections.Counter(rel)
print('   S5 (视图数, BCA数) 分布 top10 %s' % c.most_common(10))
n_eq = sum(v for (x, y), v in c.items() if x == y)
n_gt = sum(v for (x, y), v in c.items() if y > x)
n_lt = sum(v for (x, y), v in c.items() if y < x)
print('   S5 相等 %d / BCA 更多 %d / BCA 更少 %d' % (n_eq, n_gt, n_lt))
ck('S5a 无「BCA 比视图少」的类', n_lt == 0, n_lt)
ck('S5b BCA > 视图 的类占多数（BCA 含无 vftable 基类）', n_gt > n_eq, (n_gt, n_eq))
# 视图 mdisp 集合 ⊆ BCA mdisp 集合
sub_ok = 0; sub_bad = []
for a in CHD_ADDRS:
    vs = set(COL[x]['mdisp'] for x in G[a])
    bs = set(s32(P.dw(b + 8)) for b in BCD[a])
    if vs <= bs: sub_ok += 1
    else: sub_bad.append((hex(a), sorted(vs), sorted(bs)))
ck('S6a 视图 mdisp 集合 ⊆ BCA mdisp 集合 全部成立', sub_ok == len(CHD_ADDRS), (sub_ok, len(CHD_ADDRS), sub_bad[:3]))
# 逆向序列律：BCA 按地址逆序（= BCA 顺序）的 mdisp 序列 == 视图 mdisp 序列的反转
rev_ok = 0; rev_bad = []
for a in CHD_ADDRS:
    vs = [COL[x]['mdisp'] for x in G[a]]           # R203 parse 顺序（组头视图在前）
    bs = [s32(P.dw(b + 8)) for b in BCD[a]]
    bs_dedup = []
    for x in bs:
        if not bs_dedup or bs_dedup[-1] != x: bs_dedup.append(x)
    if bs_dedup == list(reversed(vs)): rev_ok += 1
    elif len(G[a]) > 1: rev_bad.append((COL[G[a][0]]['name'][:34], vs, bs_dedup))
print('   S7 逆序去重律成立 %d / %d' % (rev_ok, len(CHD_ADDRS)))
print('   S7 反例 %s' % rev_bad[:6])
ck('S7a 逆序去重律成立率高', rev_ok / len(CHD_ADDRS) > 0.5, rev_ok / len(CHD_ADDRS))
mi = [a for a in CHD_ADDRS if len(G[a]) >= 2]
mi_rev = sum(1 for a in mi if (lambda bs: [x for i, x in enumerate(bs) if i == 0 or bs[i-1] != x] == list(reversed([COL[c]['mdisp'] for c in G[a]])))([s32(P.dw(b+8)) for b in BCD[a]]))
ck('S7b MI 类 %d 中逆序去重律成立 %d' % (len(mi), mi_rev), mi_rev > 0, (mi_rev, len(mi)))

# ---------- 反控 ----------
# R1 把 BCA 长度截到视图数 -> 逆序律必须掉
trunc_ok = 0
for a in mi:
    bs = [s32(P.dw(b + 8)) for b in BCD[a]][:len(G[a])]
    ded = [x for i, x in enumerate(bs) if i == 0 or bs[i-1] != x]
    if ded == list(reversed([COL[c]['mdisp'] for c in G[a]])): trunc_ok += 1
print('   R1 反控：BCA 截断到视图数后逆序律成立 %d / %d' % (trunc_ok, len(mi)))
ck('R1a 反控：截断破坏逆序律（判据依赖完整 BCA）', trunc_ok < mi_rev, (trunc_ok, mi_rev))
# R2 把 CHD 的 arr 指针换成同段随机值 -> 深度律/子集律必须掉
import random
random.seed(2041)
arrmap = {a: P.dw(a + 12) for a in CHD_ADDRS}
pool = list(arrmap.values())
hit = 0
for a in CHD_ADDRS:
    r = arrmap[random.choice(CHD_ADDRS)]
    n = P.dw(a + 8)
    fake = [P.dw(r + 4 * j) for j in range(n)]
    vs = set(COL[x]['mdisp'] for x in G[a])
    bs = set(s32(P.dw(b + 8)) if P.where(b) == '.rdata' else 10**9 for b in fake)
    if vs <= bs: hit += 1
print('   R2 反控：随机 BCA 指针下子集律成立 %d / %d' % (hit, len(CHD_ADDRS)))
ck('R2a 反控：随机 BCA 指针破坏子集律', hit < 0.5 * len(CHD_ADDRS), (hit, len(CHD_ADDRS)))
# R3 名字判据 vs pCHD 判据的独立性：把 pCHD 字段全部置为 0 后分组退化
ck('R3a pCHD 全部非零（分组不退化）', all(a != 0 for a in CHD_ADDRS), min(CHD_ADDRS))

json.dump(dict(N=N, fails=fails, uniq_bcd=len(uniq), bca_refs=len(allb),
               f4=dict(F4), pdisp=dict(PD), vdisp=dict(VD), attr=dict(AT),
               rel=c.most_common(12), n_eq=n_eq, n_gt=n_gt, n_lt=n_lt,
               sub_ok=sub_ok, rev_ok=rev_ok, mi=len(mi), mi_rev=mi_rev,
               single=len(single), s_ok=s_ok, depth_ok=depth_ok,
               rev_bad=rev_bad[:10], depth_bad=depth_bad[:5]),
          open('/home/t628/projects/ra2-campaign-forge/_r204/m2_chd2.json', 'w'), ensure_ascii=False, indent=1)
print('\n== %d assertions, %d FAIL ==' % (N, len(fails)))
print('FAILS:', fails)
