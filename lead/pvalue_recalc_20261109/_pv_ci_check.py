# -*- coding: utf-8 -*-
# _pv_ci_check.py — 修正 _pv_recompute.py 中 CP 二分方向错误，独立复算三口径 CP/Wilson CI 与 bootstrap
# 说明：_pv_recompute.py 的 cp_two_sided() 两处判反（k=n 时 sf 随 p 递增，却写 lo=m；
#       上界 cdf(k=n,n,p)≡1 恒 > alpha/2 使 hi 塌到 0）。本脚本用闭式 + 校正二分重算。
import math, json, random
from fractions import Fraction
from statistics import NormalDist

alpha = 0.05
a2 = alpha / 2

def sf(k, n, p):
    return sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(k, n + 1))

def cdf(k, n, p):
    return sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(0, k + 1))

def cp_two_sided_fixed(n, k):
    # 下界：解 sf(k,n,p_lo)=alpha/2；sf 随 p 递增 => 若 sf(m)>a2 说明 m 太大 => hi=m
    lo, hi = 0.0, 1.0
    for _ in range(200):
        m = (lo + hi) / 2
        if sf(k, n, m) > a2: hi = m
        else: lo = m
    p_lo = (lo + hi) / 2
    # 上界：解 cdf(k,n,p_hi)=alpha/2；k=n 时 cdf≡1，无内点解 => CP 上界 = 1（闭式）
    p_hi = 1.0 if k == n else None
    if p_hi is None:
        lo, hi = 0.0, 1.0
        for _ in range(200):
            m = (lo + hi) / 2
            if cdf(k, n, m) > a2: lo = m
            else: hi = m
        p_hi = (lo + hi) / 2
    return p_lo, p_hi

def wilson(n, k, z):
    ph = k / n
    den = 1 + z * z / n
    cen = (ph + z * z / (2 * n)) / den
    half = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return max(0.0, cen - half), min(1.0, cen + half)

z = NormalDist().inv_cdf(0.975)
print('=== 修正后 CP 95% 双侧 / Wilson 95% ===')
print('z =', z, ' alpha/2 =', a2)
for n in (18, 16, 3):
    k = n
    lo, hi = cp_two_sided_fixed(n, k)
    lo_closed = a2 ** (1.0 / n)
    wlo, whi = wilson(n, k, z)
    print('n =', n, 'k =', k)
    print('  CP95 (二分)   = [', lo, ',', hi, ']')
    print('  CP95 (闭式)   = [', lo_closed, ', 1.0]   (a2)^(1/n) =', lo_closed)
    print('  校验 sf(n,n,lo_closed) =', sf(n, n, lo_closed), ' 应 = ', a2)
    print('  Wilson95      = [', wlo, ',', whi, ']')
    p_two = min(1.0, 2 * (0.5 ** n))
    print('  双侧 exact p  =', p_two, ' = 2*2^-' + str(n))

print()
print('=== bootstrap 配对正确率差（68 条冻结，seed=20261109, 200000 次） ===')
# 构造 68 条冻结行的 (c72, c74) 配对，增益 18 条 (0,1)、其余 50 条 (1,1) 或 (0,0)
# 依据 _pv_recompute.py PART1 实测：frozen chain72=48 chain74=66, b=18 c=0
# 因此 66 条 74 正确、48 条 72 正确；交集 48 条 (1,1)、18 条 (0,1)、2 条 (0,0)
pairs = [(1, 1)] * 48 + [(0, 1)] * 18 + [(0, 0)] * 2
print('len(pairs) =', len(pairs), 'sum c72 =', sum(x[0] for x in pairs),
      'sum c74 =', sum(x[1] for x in pairs), 'mean diff =', sum(x[1]-x[0] for x in pairs)/68)
rnd = random.Random(20261109)
N = 200000
diffs = []
for _ in range(N):
    s = 0
    for _j in range(68):
        x, y = pairs[rnd.randrange(68)]
        s += y - x
    diffs.append(s / 68)
diffs.sort()
lo = diffs[int(0.025 * N)]
hi = diffs[int(0.975 * N)]
print('bootstrap 200000 percentile 95% CI = [', lo, ',', hi, ']')
print('(上游 SCORE_DECOMP.md:162 记 [0.16176470588235295, 0.36764705882352944])')
