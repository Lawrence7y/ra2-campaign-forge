# -*- coding: utf-8 -*-
# _pvv_recalc.py — 独立复核：从两份回归 JSON 原始 rows[] 重新推导配对计数、三口径 p、CI、设计效应、数量级
# 不 import 任何 _pv_ 脚本；不调用 scipy；纯 math + fractions + random。
import math, json, random
from fractions import Fraction
from statistics import NormalDist
from collections import Counter

ROOT = r"D:/Project/ra2-campaign-forge"
P1 = ROOT + "/lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json"   # 72 版（v1 并集）
P2 = ROOT + "/lead/gate_pipeline_20261109/_gp_regression_out.json"             # 74 版（v2 逐 span）

V1 = json.load(open(P1, encoding="utf-8"))
V2 = json.load(open(P2, encoding="utf-8"))
a, b = {r["id"]: r for r in V1["rows"]}, {r["id"]: r for r in V2["rows"]}
common = sorted(set(a) & set(b))
print("common =", len(common), "onlyA =", sorted(set(a) - set(b)), "onlyB =", sorted(set(b) - set(a)))

all1 = {r["id"] for r in V1["rows"]}
all2 = {r["id"] for r in V2["rows"]}
s1 = sum(1 for r in V2["rows"] if r["chain"] == r["expect"])
s2 = sum(1 for r in V1["rows"] if r["chain"] == r["expect"])
print(f"s(74,all74) = {s1} s(72,all72) = {s2} total delta = {s1 - s2}")
flips = sorted(i for i in common if a[i]["expect"] != b[i]["expect"])
print("flips =", len(flips), flips)

# 冻结子集：common 中剔除翻标，且 id/text_head/tokens/expect 与四个单层输出列逐行相同
strict = []
for i in common:
    if i in flips: continue
    r1, r2 = a[i], b[i]
    same = all(r1.get(k) == r2.get(k) for k in ("text_head", "tokens", "expect", "naive", "r10", "r12", "n13"))
    if same: strict.append(i)
print("n_frozen =", len(strict))
print("strict all four single layers identical?", all(
    a[i].get(k) == b[i].get(k) for i in strict for k in ("naive", "r10", "r12", "n13")))

c72 = [1 if a[i]["chain"] == a[i]["expect"] else 0 for i in strict]
c74 = [1 if b[i]["chain"] == b[i]["expect"] else 0 for i in strict]
print(f"frozen: chain72 = {sum(c72)} chain74 = {sum(c74)} delta = {sum(c74) - sum(c72)}")
bb = sum(1 for x, y in zip(c72, c74) if x == 0 and y == 1)
cc = sum(1 for x, y in zip(c72, c74) if x == 1 and y == 0)
disc = bb + cc
print(f"paired b = {bb} c = {cc} n_discordant = {disc}")
print("b-c == frozen delta ?", bb - cc == sum(c74) - sum(c72))
print("paired accuracy diff =", Fraction(bb - cc, len(strict)), "=", (bb - cc) / len(strict))

gains = [i for i in strict if a[i]["chain"] != b[i]["chain"] and c72[strict.index(i)] == 0]
losses = [i for i in strict if a[i]["chain"] != b[i]["chain"] and c72[strict.index(i)] == 1]
print("gains =", len(gains), "losses =", len(losses))
print("all gains expect == PASS ?", all(a[i]["expect"] == "PASS" for i in gains))
print("all gains 72chain CATCH -> 74chain PASS ?", all(a[i]["chain"] == "CATCH" and b[i]["chain"] == "PASS" for i in gains))
print("all gains 72/74 expect same?", all(a[i]["expect"] == b[i]["expect"] for i in gains))

texts = [a[i]["text_head"] for i in gains]
cnt = Counter(texts)
dups = [{"text": t, "count": c} for t, c in cnt.items() if c > 1]
print("n_distinct_texts =", len(cnt), "of", len(gains))
print("dup_texts =", dups)
for t, c in cnt.items():
    if c > 1:
        print("  dup ids for", repr(t), "=", [i for i in gains if a[i]["text_head"] == t])
fams = Counter(a[i]["family"] for i in gains)
print("families =", dict(fams), "n_families =", len(fams))
# 定向修复集：72 版 frozen 内 FP (expect PASS 而 chain CATCH)
fp72 = [i for i in strict if a[i]["expect"] == "PASS" and a[i]["chain"] == "CATCH"]
fp74 = [i for i in fp72 if b[i]["expect"] == "PASS" and b[i]["chain"] == "CATCH"]
print("72 FP in frozen =", len(fp72), "74 still FP =", len(fp74), fp74)
print("repaired =", len(fp72) - len(fp74))
print("gains set == repaired set ?", set(gains) == set(fp72) - set(fp74))

print()
print("=== 三口径双侧 exact binomial（小 p 值法） ===")
def p_exact_two(n, k):
    # min(1, 2 * P(X>=k | Bin(n,0.5)))，用 Fraction 精确算
    tail = sum(Fraction(math.comb(n, j), 2 ** n) for j in range(k, n + 1))
    return min(Fraction(1), 2 * tail)

for label, n in (("all_units", 18), ("distinct_texts", 16), ("family_level", 3)):
    k = n
    p = p_exact_two(n, k)
    print(f"{label} n={n} k={k} p_two exact = {p} = {float(p)!r}   2^(1-n) = {float(Fraction(2, 2**n))!r}")
print("one-sided n=18 =", float(Fraction(1, 2 ** 18)))

print()
print("=== Clopper-Pearson 95% 双侧（闭式 + 独立二分校验）===")
alpha = 0.05
a2 = alpha / 2
def binom_sf(k, n, p):
    return sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(k, n + 1))
def binom_cdf(k, n, p):
    return sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(0, k + 1))
for n in (18, 16, 3):
    k = n
    lo_closed = a2 ** (1.0 / n)
    # 独立二分：解 sf(k,n,p)=a2（sf 随 p 递增）
    lo, hi = 0.0, 1.0
    for _ in range(300):
        m = (lo + hi) / 2
        if binom_sf(k, n, m) > a2: hi = m
        else: lo = m
    lo_bis = (lo + hi) / 2
    print(f"n={n} k={k} CP95 lower (closed) = {lo_closed!r}")
    print(f"           CP95 lower (bisect) = {lo_bis!r}")
    print(f"           check sf(n,n,lo_closed) = {binom_sf(n,n,lo_closed)!r} (target {a2!r})")
    print(f"           CP95 upper = 1.0 (k=n: cdf≡{binom_cdf(n,n,0.5)!r}, 无内点解)")

print()
print("=== Wilson 95% ===")
z = NormalDist().inv_cdf(0.975)
print("z =", z)
for n in (18, 16, 3):
    k = n
    ph = k / n
    den = 1 + z * z / n
    cen = (ph + z * z / (2 * n)) / den
    half = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    print(f"n={n} Wilson95 = [{max(0.0,cen-half)!r}, {min(1.0,cen+half)!r}]")
print("CP/Wilson lower contains 0.5 ?", all(a2 ** (1.0/n) < 0.5 for n in (18,16,3)))

print()
print("=== 数量级 ===")
p18 = float(p_exact_two(18, 18)); p16 = float(p_exact_two(16, 16)); p3 = float(p_exact_two(3, 3))
print("family/all ratio =", p3 / p18, "= 2^", math.log2(p3 / p18))
print("log10 diff =", math.log10(p3 / p18))
print("distinct/all ratio =", p16 / p18)
print("log10(2^15) =", 15 * math.log10(2))

print()
print("=== 设计效应 n_eff = n/(1+(n-1)rho), n=18 ===")
n = 18
for rho in (0.0, 0.3, 0.5, 0.8, 0.9, 1.0):
    ne = n / (1 + (n - 1) * rho)
    deff = 1 + (n - 1) * rho
    fl = math.floor(ne)
    p_floor = min(1.0, 2 * 0.5 ** fl)
    print(f"rho={rho} n_eff={ne:.10f} deff={deff:.10f} floor(n_eff)={fl} p_two(floor)={p_floor!r}")
ne1 = n / (1 + (n - 1) * 1.0)
print(f"rho=1 -> n_eff={ne1!r} p_two(n_eff=1,k=1)={float(p_exact_two(1,1))!r}")
print("p from 7.62939453125e-06 to 1.0 ratio =", 1.0 / p18, "log10 =", math.log10(1.0 / p18))
thr = math.log2(40)
print("2*2^-n_eff < 0.05 => n_eff > log2(40) =", thr)
print("continuous: rho <", (n / thr - 1) / (n - 1))
print("discrete n_eff>=6: rho <=", Fraction(2, 17), "=", 2 / 17)
print("check n_eff at rho=2/17 =", n / (1 + (n - 1) * (2 / 17)))
print("check n_eff at rho=0.14013134380964332 =", n / (1 + (n - 1) * 0.14013134380964332))

print()
print("=== bootstrap 配对正确率差（seed=20261109, 200000 次） ===")
pairs = [(c72[j], c74[j]) for j in range(len(strict))]
print("len(pairs) =", len(pairs), "counts =", dict(Counter(pairs)))
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
print("bootstrap 200000 percentile 95% CI = [", diffs[int(0.025 * N)], ",", diffs[int(0.975 * N)], "]")
