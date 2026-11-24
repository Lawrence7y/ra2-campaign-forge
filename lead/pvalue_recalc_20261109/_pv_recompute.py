# -*- coding: utf-8 -*-
# _pv_recompute.py — 独立重算：配对 b/c、三口径 p 与 CI、设计效应、GP-A1/A2/A3 复核
# 零真机 / 零采样 / 只读上游两件 JSON；不改任何脚本、语料、产物。
# 用法: python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/pvalue_recalc_20261109/_pv_recompute.py"
import json, math, hashlib
from fractions import Fraction
from collections import Counter
from statistics import NormalDist

BASE = 'D:/Project/ra2-campaign-forge/'
P74 = BASE + 'lead/gate_pipeline_20261109/_gp_regression_out.json'
P72 = BASE + 'lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json'

def load(p):
    return json.load(open(p, encoding='utf-8'))

d74, d72 = load(P74), load(P72)
r74 = {x['id']: x for x in d74['rows']}
r72 = {x['id']: x for x in d72['rows']}

print('=== PART 0: 上游两件指纹（hashlib 实算） ===')
for tag, p in [('74', P74), ('72', P72)]:
    b = open(p, 'rb').read()
    print(tag, 'sha256 =', hashlib.sha256(b).hexdigest(), 'bytes =', len(b))
print('corpus_n 74 =', d74['corpus_n'], 'rows =', len(d74['rows']))
print('corpus_n 72 =', d72['corpus_n'], 'rows =', len(d72['rows']))

print()
print('=== PART 1: 配对 b/c 与 frozen68 构造（独立复现） ===')
A, B = set(r74), set(r72)
common = A & B
onlyA = sorted(A - B)
onlyB = sorted(B - A)
print('common =', len(common), 'onlyA =', onlyA, 'onlyB =', onlyB)

def score(rows, ids, col='chain'):
    return sum(1 for i in ids if rows[i][col] == rows[i]['expect'])

s74 = score(r74, A)
s72 = score(r72, B)
print('s(74,all74) =', s74, 's(72,all72) =', s72, 'total delta =', s74 - s72)

flips = sorted(i for i in common if r74[i]['expect'] != r72[i]['expect'])
print('flips (expect changed) =', len(flips), flips)
F = sorted(common - set(flips))
print('n_frozen =', len(F))

pairs = []
for i in F:
    c72 = r72[i]['chain'] == r72[i]['expect']
    c74 = r74[i]['chain'] == r74[i]['expect']
    pairs.append((i, c72, c74, r72[i]['chain'], r74[i]['chain'], r74[i]['expect']))
b = sum(1 for x in pairs if (not x[1]) and x[2])
c = sum(1 for x in pairs if x[1] and (not x[2]))
n_disc = b + c
print('frozen: chain72 =', score(r72, F), 'chain74 =', score(r74, F), 'delta =', score(r74, F) - score(r72, F))
print('paired b =', b, 'c =', c, 'n_discordant =', n_disc)
print('b-c == frozen delta ?', b - c == score(r74, F) - score(r72, F))

gains = [x for x in pairs if (not x[1]) and x[2]]
losses = [x for x in pairs if x[1] and (not x[2])]
print('gains =', len(gains), 'losses =', len(losses))
print('gain ids =', [x[0] for x in gains])
print('all gains expect == PASS ?', all(x[5] == 'PASS' for x in gains))
print('all gains 72chain CATCH -> 74chain PASS ?', all(x[3] == 'CATCH' and x[4] == 'PASS' for x in gains))

heads = [r74[x[0]]['text_head'] for x in gains]
hc = Counter(heads)
dups = {k: v for k, v in hc.items() if v > 1}
print('n_distinct_texts =', len(hc), 'of', len(heads))
print('dup_texts =', json.dumps([{'text': k, 'count': v} for k, v in dups.items()], ensure_ascii=False))
for k in dups:
    print('  dup ids for', repr(k), '=', [x[0] for x in gains if r74[x[0]]['text_head'] == k])

fam = Counter(r74[x[0]]['family'] for x in gains)
print('families =', dict(fam), 'n_families =', len(fam))

fp72 = [i for i in F if r72[i]['expect'] == 'PASS' and r72[i]['chain'] == 'CATCH']
fp74 = [i for i in F if r74[i]['expect'] == 'PASS' and r74[i]['chain'] == 'CATCH']
print('72 FP in frozen =', len(fp72), '74 still FP =', len(fp74), fp74)
print('repaired =', len(set(fp72) - set(fp74)))

print()
print('=== PART 1d: GP-A1/A2/A3 两版 chain 值 ===')
for gid in ['GP-A1', 'GP-A2', 'GP-A3']:
    a = r74.get(gid)
    print('74', gid, 'present =', a is not None, 'expect =', a['expect'] if a else None,
          'chain =', a['chain'] if a else None, 'naive/r10/r12/n13 =',
          [a[k] for k in ('naive','r10','r12','n13')] if a else None,
          'text_head =', repr(a['text_head']) if a else None)
for gid in ['GP-C03']:
    a = r72.get(gid)
    print('72', gid, 'present =', a is not None, 'expect =', a['expect'] if a else None,
          'chain =', a['chain'] if a else None, 'naive/r10/r12/n13 =',
          [a[k] for k in ('naive','r10','r12','n13')] if a else None,
          'text_head =', repr(a['text_head']) if a else None)
print('GP-C03[72] vs GP-A1[74] text_head equal ?', r72['GP-C03']['text_head'] == r74['GP-A1']['text_head'])

print()
print('=== PART 2: exact binomial 双侧 p（小 p 值法） ===')
def binom_sf(k, n):
    # P(X >= k), X ~ Bin(n, 1/2)
    return sum((Fraction(math.comb(n, j), 2 ** n) for j in range(k, n + 1)), Fraction(0))

def p_two_sided(n, k):
    return min(Fraction(1), 2 * binom_sf(k, n))

for n, label in [(18, 'all_units'), (16, 'distinct_texts'), (3, 'family_level')]:
    k = n
    p = p_two_sided(n, k)
    print(label, 'n =', n, 'k =', k, 'P(X>=n) =', str(binom_sf(n, n)), '=', float(binom_sf(n, n)),
          'p_two exact =', str(p), 'p_two float =', float(p))

print()
print('=== PART 2 CI: Clopper-Pearson 95% 双侧（k=n 闭式 + 二分数值校验） ===')
alpha2 = 0.025
def cp_two_sided(n, k, alpha=0.05):
    # 双侧 CP：下界解 P(X>=k | p_lo) = alpha/2；上界解 P(X<=k | p_hi) = alpha/2
    def sf(k, n, p):
        return sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(k, n + 1))
    def cdf(k, n, p):
        return sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(0, k + 1))
    lo, hi = 0.0, 1.0
    for _ in range(200):
        m = (lo + hi) / 2
        if sf(k, n, m) > alpha / 2: lo = m
        else: hi = m
    p_lo = (lo + hi) / 2
    lo, hi = 0.0, 1.0
    for _ in range(200):
        m = (lo + hi) / 2
        if cdf(k, n, m) > alpha / 2: hi = m
        else: lo = m
    p_hi = (lo + hi) / 2
    return p_lo, p_hi

for n, label in [(18, 'all_units n=18'), (16, 'distinct_texts n=16'), (3, 'family_level n=3')]:
    k = n
    lo, hi = cp_two_sided(n, k)
    lo_closed = (alpha2) ** (1.0 / n)   # k=n: (alpha/2)^(1/n)
    print(label, 'CP95 = [', lo, ',', hi, '] closed-form lo =', lo_closed,
          'sf(k,p_lo) =', sum(math.comb(n, j) * lo ** j * (1 - lo) ** (n - j) for j in range(k, n + 1)))

print()
print('=== PART 2d: 数量级对比 ===')
ps = {n: float(p_two_sided(n, n)) for n in (18, 16, 3)}
base = ps[18]
for n in (18, 16, 3):
    print('n =', n, 'p =', ps[n], 'vs n=18 ratio =', ps[n] / base,
          'log10(p) =', math.log10(ps[n]))

print()
print('=== PART 3: 设计效应 n_eff = n/(1+(n-1)*rho) ===')
for rho in (0.0, 0.3, 0.5, 0.8, 0.9, 1.0):
    ne = 18.0 / (1.0 + (18 - 1) * rho)
    print('rho =', rho, 'n_eff =', ne, 'rounded4 =', round(ne, 4),
          'deff = 1+(n-1)rho =', 1.0 + 17 * rho)
print('rho=1 -> n_eff =', 18.0 / 18, 'p_two(n_eff=1, k=1) =', float(p_two_sided(1, 1)),
      '= 2*P(X>=1|Bin(1,0.5)) = 2*0.5 = 1.0 (min(1,...) )')
for nf in (1, 2, 3):
    print('if n_eff floored to', nf, ': p_two =', float(p_two_sided(nf, nf)))

print()
print('=== PART 4c: post-selection 条件信息量 ===')
# 在「已知这18条是K9失败样本」条件下观测18/18修好：条件概率≈1，自信息 -log2(1)=0
print('P(18/18 repaired | selected as K9 failure set) ~ 1.0 (by construction)')
print('surprisal = -log2(P) = 0 bits; likelihood ratio vs H0(0.5^18) is NOT identifiable post-selection')

print()
print('=== PART 6: Wilson 95% 与 bootstrap 配对差（复现上游） ===')
z = NormalDist().inv_cdf(0.975)
print('z =', z)
for n, label in [(18, 'n=18'), (16, 'n=16'), (3, 'n=3')]:
    ph = n / n
    den = 1 + z * z / n
    cen = (ph + z * z / (2 * n)) / den
    half = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    print(label, 'Wilson95 = [', cen - half, ',', min(1.0, cen + half), ']')
print('paired acc diff 18/68 =', 18.0 / 68, 'normal SE sqrt(p(1-p)/68) =', math.sqrt((18/68)*(50/68)/68))
