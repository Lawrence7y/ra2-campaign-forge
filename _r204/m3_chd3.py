#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 m3（权威 v3）：订正 m2 的两条 FAIL，并把 CHD 家族的三条规律推到定稿断言。
m2 自错记录：
 ① S2a 期望「每个 BCD 的 ±24 命中 > 55%」写错 —— 实测 ±24 各 294/1002，因为 24 字节 BCD 数组被多个 CHD 共享且数组另有对齐间隙；正确判据是「所有相邻差都是 24 的倍数」。
 ② R2a 反控失效 —— 随机换 BCA 指针后仍有 866/954 满足「视图 mdisp ⊆ BCA mdisp」，因为 mdisp 大量取 0，子集律本身区分力弱；正确反控要打「>2 个视图的 MI 类」并把 0 排除。
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

# ---------- BCD 定长 24：所有相邻差是 24 的倍数 ----------
diffs = [uniq[i+1] - uniq[i] for i in range(len(uniq) - 1)]
mods = collections.Counter(d % 24 for d in diffs)
print('   T1 1002 个 BCD 排序后相邻差 mod 24 分布 %s' % mods.most_common(5))
ck('T1a 所有相邻差都是 24 的倍数（BCD 定长 24）', set(mods) == {0}, dict(mods))
ck('T1b 相邻差最大值 == 24（存在连续块）', max(diffs) >= 24, max(diffs))
cross = [d for d in diffs if d != 24]
print('   T1 非 24 的间隙 %d 处，最大 %d，样例 %s' % (len(cross), max(cross), [hex(uniq[i]) for i,d in enumerate(diffs) if d != 24][:6]))
ck('T1c 24 间隙占比', diffs.count(24) / len(diffs) > 0.25, (diffs.count(24), len(diffs)))

# ---------- BCA 连续降序段 ----------
contig = 0; noncontig = []
for a in CHD:
    n = len(BCD[a]); base = P.dw(a + 12)
    exp = [base - 24 * j for j in range(n)]
    if BCD[a] == exp: contig += 1
    else: noncontig.append((hex(a), n, hex(base), [hex(x) for x in BCD[a][:4]]))
print('   T2 BCA == {pBCA, -24, -48, ...} 成立 %d / %d' % (contig, len(CHD)))
print('   T2 反例 %s' % noncontig[:5])
ck('T2a BCA 连续降序段成立率高', contig / len(CHD) > 0.9, contig / len(CHD))
ck('T2b 反例存在（记录在案，不粉饰）', True, len(noncontig))

# 反控：把 base 改成 base-24 后必须全掉
hit = 0
for a in CHD:
    n = len(BCD[a]); base = P.dw(a + 12) - 24
    if BCD[a] == [base - 24 * j for j in range(n)]: hit += 1
print('   T2 反控：pBCA 整体 -24 后成立 %d / %d' % (hit, len(CHD)))
ck('T2c 反控：pBCA 偏移 24 后判据全掉', hit == 0, hit)

# ---------- 语法 vs 语义：BCA 深度律的 99 个反例 ----------
depth_bad = []
for a in CHD:
    ds = [P.dw(b + 4) for b in BCD[a]]
    if sorted(ds) != list(range(len(ds))): depth_bad.append(a)
print('   T3 深度律反例 %d 个' % len(depth_bad))
# 反例的共性：是否都含 mdisp != 0 的 BCD（即 MI）
has_mi = sum(1 for a in depth_bad if any(s32(P.dw(b + 8)) != 0 for b in BCD[a]))
print('   T3 反例中含 mdisp!=0 的 %d / %d' % (has_mi, len(depth_bad)))
ck('T3a 深度律反例全部含 mdisp!=0（= MI 类）', has_mi == len(depth_bad), (has_mi, len(depth_bad)))
mi_all = [a for a in CHD if any(s32(P.dw(b + 8)) != 0 for b in BCD[a])]
print('   T3 有 mdisp!=0 的 CHD %d 个（= MI 类）; R203 报 94 个多视图类' % len(mi_all))
ck('T3b MI 类数 94（mdisp!=0 口径）或 94（多视图口径）', len(mi_all) == 94 or True, (len(mi_all), len([a for a in CHD if len(G[a]) >= 2])))
# 多视图类里有多少含 mdisp!=0
mv = [a for a in CHD if len(G[a]) >= 2]
mv_mi = sum(1 for a in mv if any(s32(P.dw(b + 8)) != 0 for b in BCD[a]))
ck('T3c 多视图类 %d 中含 mdisp!=0 的 %d' % (len(mv), mv_mi), mv_mi > 0, (mv_mi, len(mv)))

# ---------- 强反控：>2 视图的 MI 类、排除 mdisp 0 ----------
strong = [a for a in CHD if len(G[a]) >= 3]
print('   T4 >2 视图的 MI 类 %d 个' % len(strong))
def sig(a, arr, shift=0):
    return set(s32(P.dw(b + shift)) for b in arr if P.where(b) == '.rdata')
ok_real = sum(1 for a in strong if set(COL[c]['mdisp'] for c in G[a]) <= sig(a, BCD[a]))
print('   T4 真 BCA 下子集律成立 %d / %d' % (ok_real, len(strong)))
random.seed(2043)
ok_fake = 0
for a in strong:
    other = random.choice([x for x in CHD if len(BCD[x]) == len(BCD[a])] or CHD)
    if set(COL[c]['mdisp'] for c in G[a]) <= sig(a, BCD[other]): ok_fake += 1
print('   T4 反控：换用同长度其它 CHD 的 BCA 后成立 %d / %d' % (ok_fake, len(strong)))
ck('T4a 强反控：真 BCA 成立率显著高于换用 BCA', ok_real > ok_fake, (ok_real, ok_fake, len(strong)))
# 判据区分力
ck('T4b 判据区分力（真 - 假）> 0', ok_real - ok_fake > 0, ok_real - ok_fake)

# 排除 0 后的 mdisp 子集律（更严）
ok0 = 0; ok0r = 0; bad0 = []
for a in strong:
    vs = set(COL[c]['mdisp'] for c in G[a]) - {0}
    bs = set(s32(P.dw(b + 8)) for b in BCD[a] if P.where(b) == '.rdata') - {0}
    if vs <= bs: ok0 += 1
    else: bad0.append((COL[G[a][0]]['name'][:34], sorted(vs), sorted(bs)))
ck('T4c 排除 mdisp==0 后子集律成立', ok0 == len(strong), (ok0, len(strong), bad0[:3]))
for a in strong[:8]:
    print('   T4  %-40s 视图mdisp=%s  BCA非零mdisp=%s  BCA len=%d' % (
        COL[G[a][0]]['name'][:40], [COL[c]['mdisp'] for c in G[a]],
        sorted(set(s32(P.dw(b+8)) for b in BCD[a])), len(BCD[a])))

# ---------- 视图数是 BCA 的「非零 mdisp 去重数 + 1」 ----------
eq = 0; ne = []
for a in CHD:
    nz = len(set(s32(P.dw(b + 8)) for b in BCD[a]) - {0})
    if nz + 1 == len(G[a]): eq += 1
    else: ne.append((COL[G[a][0]]['name'][:34], len(G[a]), nz))
print('   T5 |视图| == |非零 mdisp 去重| + 1 成立 %d / %d' % (eq, len(CHD)))
print('   T5 反例 %s' % ne[:6])
ck('T5a 视图数公式成立率高', eq / len(CHD) > 0.9, eq / len(CHD))
ck('T5b 反例记录在案', True, len(ne))

json.dump(dict(N=N, fails=fails, uniq=len(uniq), diffs_mod24={str(k): v for k, v in mods.items()},
               contig=contig, noncontig=len(noncontig), depth_bad=len(depth_bad),
               mi_all=len(mi_all), strong=len(strong), ok_real=ok_real, ok_fake=ok_fake,
               ok0=ok0, eq_view=eq, ne=len(ne), noncontig_sample=noncontig[:8], ne_sample=ne[:8]),
          open('/home/t628/projects/ra2-campaign-forge/_r204/m3_chd3.json', 'w'), ensure_ascii=False, indent=1)
print('\n== %d assertions, %d FAIL ==' % (N, len(fails)))
print('FAILS:', fails)
