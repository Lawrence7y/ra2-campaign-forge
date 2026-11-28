#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 m4（权威 v4）：把 CHD/BCD 布局钉死。订正 m3 三处自错：
 E1 T2 的期望式写错（把 pBCA 当数组首元素，实测 pBCA 指向的是「装有 BCD 指针的数组」，值与 pBCA 相邻而非相等）；
 E2 T4 的 sig(shift=0) 读成 pTD 而非 mdisp（应为 +8），致「真 BCA 0/84」；
 E3 T1 的 mod 24 断言方向：先看精确差分直方图与数组边界，不要预设全局同一网格。
"""
import sys, struct, collections, json, random
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
        COL[base + 4 * i] = dict(mdisp=s32(w[i+1]), pchd=w[i+4], name=nm.decode('latin1'))
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
ck('U0 基数 COL1214/VTI1214/CHD954/BCD1002/BCA2615', (len(COL),len(VTI),len(G),len(uniq))==(1214,1214,954,1002) and sum(len(v) for v in BCD.values())==2615,
   (len(COL),len(VTI),len(G),len(uniq),sum(len(v) for v in BCD.values())))

# ---- E-A 组内差分（同一 CHD 的 BCA 相邻元素） ----
within = collections.Counter()
for a, v in BCD.items():
    for i in range(len(v)-1): within[v[i+1]-v[i]] += 1
print('   A 组内相邻差分 top8 %s' % within.most_common(8))
ck('A1a 组内相邻差分 -24 主导', within.most_common(1)[0][0] == -24, within.most_common(3))
ck('A1b -31104 类大跳存在（记录）', within[-31104] > 0, within[-31104])
# 大跳样例
big = [(hex(a), [hex(x) for x in v]) for a, v in BCD.items() if any(v[i+1]-v[i] != -24 for i in range(len(v)-1))][:3]
print('   A 非 -24 组样例:')
for k, v in big: print('     ', k, v[:8])

# ---- E-B BCD 24 字节定长的直接证据：+24 邻居也是合法 BCD ----
def is_bcd(b):
    if P.where(b) != '.rdata': return False
    ptd = P.dw(b)
    if P.where(ptd) not in ('.data', '.rdata'): return False
    nm = P.cstr(ptd + 8, 400)
    return bool(nm and nm.startswith(b'.?A') and nm.endswith(b'@@'))
nb = sum(1 for b in uniq if is_bcd(b + 24))
nb_ = sum(1 for b in uniq if is_bcd(b - 24))
print('   B uniq 中 b+24 是合法 BCD %d/%d；b-24 是 %d/%d' % (nb, len(uniq), nb_, len(uniq)))
# 反控：随机同段地址 +24 命中率
random.seed(2044)
rnd = [P.r2o(0x7f0000) + 4 * random.randrange(0, 40000) for _ in range(2000)]
rnd = [P.B['.rdata']['lo'] + 4 * random.randrange(0, (P.B['.rdata']['rawsize'] // 4)) for _ in range(2000)]
r_hit = sum(1 for b in rnd if is_bcd(b) and is_bcd(b + 24))
print('   B 反控：随机 .rdata 地址同时是 BCD 且 +24 也是 BCD 的 %d/2000' % r_hit)
ck('B1a b+24 是合法 BCD 占比高', nb / len(uniq) > 0.8, nb / len(uniq))
ck('B1b 反控：随机地址显著更低', r_hit < nb / len(uniq) * 2000 / 2, (r_hit, nb))

# ---- E-C 全局排序差分（跨组边界造成的非 24 差） ----
diffs = [uniq[i+1]-uniq[i] for i in range(len(uniq)-1)]
dh = collections.Counter(diffs)
print('   C 全局相邻差分 top10 %s' % dh.most_common(10))
print('   C 全局差分值个数 %d，最小 %d 最大 %d' % (len(dh), min(diffs), max(diffs)))
ck('C1a 全局差分最小 == 24（无更小间隙 => 无重叠）', min(diffs) == 24, min(diffs))
ck('C1b 所有差分都是 24 的倍数', all(d % 24 == 0 for d in diffs), [d for d in diffs if d % 24][:5])
# 上面若成立则 1002 个 BCD 落在同一 24 网格
base24 = uniq[0] % 24
ck('C1c 全部 BCD 地址 == 同一 mod 24 网格', len(set(u % 24 for u in uniq)) == 1, sorted(set(u % 24 for u in uniq)))

# ---- E-D 数组结构：pBCA 指向的数组紧邻 CHD 之前？ ----
adj = 0; span = collections.Counter()
for a in CHD:
    arr = P.dw(a + 12); n = P.dw(a + 8)
    span[arr + 4 * n - a] += 1
print('   D (数组尾 - CHD 地址) 分布 top6 %s' % span.most_common(6))
ck('D1a 数组尾紧贴 CHD 起点（差 == 0）', span[0] > 900, (span[0], len(CHD)))

# ---- E-E 视图 mdisp 与 BCA mdisp（shift 修正！） ----
strong = [a for a in CHD if len(G[a]) >= 3]
def mds(arr): return set(s32(P.dw(b + 8)) for b in arr)
ok_real = sum(1 for a in strong if set(COL[c]['mdisp'] for c in G[a]) <= mds(BCD[a]))
fake_ok = 0
random.seed(2045)
for a in strong:
    cands = [x for x in CHD if len(BCD[x]) == len(BCD[a])] or CHD
    other = random.choice(cands)
    if set(COL[c]['mdisp'] for c in G[a]) <= mds(BCD[other]): fake_ok += 1
print('   E >2 视图类 %d：真 BCA 子集律 %d / 换用同长 BCA %d' % (len(strong), ok_real, fake_ok))
ck('E1a 真 BCA 子集律全部成立', ok_real == len(strong), (ok_real, len(strong)))
ck('E1b 反控：换用同长度 BCA 后成立率显著下降', fake_ok < 0.5 * len(strong), (fake_ok, len(strong)))
ck('E1c 判据区分力 = 真 - 假 > 0.5*n', (ok_real - fake_ok) > 0.5 * len(strong), ok_real - fake_ok)

# ---- E-F 「深度」字段（BCD+4）语义：排序后是否 range(n) ----
d_ok = sum(1 for a in CHD if sorted(P.dw(b + 4) for b in BCD[a]) == list(range(len(BCD[a]))))
print('   F 深度律成立 %d / %d' % (d_ok, len(CHD)))
bad = [a for a in CHD if sorted(P.dw(b + 4) for b in BCD[a]) != list(range(len(BCD[a])))]
ck('F1a 深度律反例全部是 MI 类', all(any(s32(P.dw(b+8)) != 0 for b in BCD[a]) for a in bad), len(bad))
# 反例的深度序列形态
for a in bad[:4]:
    print('   F 反例 %-34s depths=%s' % (COL[G[a][0]]['name'][:34], [P.dw(b+4) for b in BCD[a]]))
# 是否「深度 = 该 BCD 在派生链上的层号，且 MI 处重复计数」
ck('F1b 深度字段最大值 <= 该组 BCA 长度', all(max(P.dw(b+4) for b in BCD[a]) <= len(BCD[a]) for a in CHD), None)

json.dump(dict(N=N, fails=fails, within=within.most_common(12), dh=dh.most_common(12),
               nb24=nb, nb24m=nb_, r_hit=r_hit, span=span.most_common(4),
               ok_real=ok_real, fake_ok=fake_ok, strong=len(strong),
               d_ok=d_ok, bad=len(bad), uniq=len(uniq)),
          open('/home/t628/projects/ra2-campaign-forge/_r204/m4_chd4.json','w'), ensure_ascii=False, indent=1)
print('\n== %d assertions, %d FAIL ==' % (N, len(fails)))
print('FAILS:', fails)
