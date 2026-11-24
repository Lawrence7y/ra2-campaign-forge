# -*- coding: utf-8 -*-
"""V2 数字定稿：按 ask 指定的两个样本池算 ρ，并出快慢×版本×协议列联表。"""
import csv
import itertools
import json
import math
import os
import statistics
from collections import defaultdict

TRIPS = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUT = os.path.dirname(os.path.abspath(__file__))


def ff(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    dx = math.sqrt(sum((a - mx) ** 2 for a in xs))
    dy = math.sqrt(sum((b - my) ** 2 for b in ys))
    return num / (dx * dy) if dx > 0 and dy > 0 else None


def ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(xs, ys):
    return pearson(ranks(xs), ranks(ys))


def fisher(a, b, c, d):
    n = a + b + c + d
    r1, c1 = a + b, a + c

    def C(x, y):
        return 0 if (y < 0 or y > x) else math.comb(x, y)
    den = C(n, c1)
    if den == 0:
        return None
    po = C(r1, a) * C(n - r1, c1 - a) / den
    p = sum(C(r1, x) * C(n - r1, c1 - x) / den for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1)
            if C(r1, x) * C(n - r1, c1 - x) / den <= po + 1e-15)
    return p


rows = []
with open(os.path.join(OUT, "census.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["base_tag"] != "mirror":
            continue
        for k in ("live_fps", "units0", "pre_fps15", "span_s", "t_abs0", "gap_s"):
            r[k] = ff(r[k])
        r["ts"] = r["fields_ts_first"] or ""
        rows.append(r)

for r in rows:
    p = os.path.join(TRIPS, r["dir"], "measure_w%s.json" % r["window"]) if r["dir"] != "." \
        else os.path.join(TRIPS, "measure_w%s.json" % r["window"])
    if os.path.exists(p):
        j = json.load(open(p, encoding="utf-8"))
        cs = j.get("counters") or []
        def mean(k):
            v = [c.get(k) for c in cs if isinstance(c.get(k), int)]
            return sum(v) / len(v) if v else None
        r["c_units"] = mean("units")
        r["c_inf"] = mean("infantry")


def hlabel(r):
    if r["harness_sha16"]:
        return r["harness_sha16"]
    ap = r["argv_harness"] or r["harness_path"]
    if ap and "harness3" in os.path.basename(ap):
        return "harness3(sha未记录)"
    return ("name:" + os.path.basename(ap)) if ap else "UNKNOWN(无_launch_result)"


SF = {}
for d in os.listdir(TRIPS):
    pp = os.path.join(TRIPS, d, "_launch_result.json")
    if os.path.exists(pp):
        argv = json.load(open(pp, encoding="utf-8")).get("argv") or []
        SF[d] = "default"
        for i, x in enumerate(argv):
            if x == '--h7-measure-start-frame':
                SF[d] = argv[i + 1]


# ============ 池 1：ask 字面口径 units0 非空 ∧ live 可算（含负 live / 含 4s settle 窗） ============
P1 = [r for r in rows if r["units0"] is not None and r["live_fps"] is not None]
P2 = [r for r in P1 if r["live_fps"] > 0]
# ============ 池 2：严格真 25s 测量窗 ============
P3 = [r for r in rows if r["verdict"] == "ok" and r["span_s"] == 25.0
      and r["live_fps"] and r["live_fps"] > 0 and r["units0"] is not None]

print("=" * 104)
print("1) ρ 按 ask 字面口径（units0 非空 ∧ live_fps 可算）")
print("=" * 104)
for name, pl in (("池1 字面：live 可为负", P1), ("池2 字面 ∧ live>0", P2), ("池3 严格 25s 窗 ∧ live>0", P3)):
    pre = [r for r in pl if r["pre_fps15"] is not None]
    print("  %-26s n=%2d  ρ_P(pre15,live)=%+0.4f ρ_S=%+0.4f | ρ_P(units0,live)=%+0.4f ρ_S=%+0.4f" % (
        name, len(pl),
        pearson([r["pre_fps15"] for r in pre], [r["live_fps"] for r in pre]),
        spearman([r["pre_fps15"] for r in pre], [r["live_fps"] for r in pre]),
        pearson([r["units0"] for r in pl], [r["live_fps"] for r in pl]),
        spearman([r["units0"] for r in pl], [r["live_fps"] for r in pl])))
print("  注：池1 里混进 1 个 live=-383.91 的坏窗（l1_20261023e4 w1，帧计数器窗内归零 3557→0）")
print("      和 5 个 span_s=4.0 的 settle 伪窗（verdict=no_advance，不是 25s 测量窗）")

print("\n" + "=" * 104)
print("2) 固定 harness 版本内 ρ(units0, live)（池3 严格窗）")
print("=" * 104)
hv = defaultdict(list)
for r in P3:
    hv[hlabel(r)].append(r)
for h, rs in sorted(hv.items(), key=lambda x: min(y["ts"] for y in x[1])):
    us = sorted(set(int(x["units0"]) for x in rs))
    ls = sorted(x["live_fps"] for x in rs)
    rp = pearson([x["units0"] for x in rs], [x["live_fps"] for x in rs]) if len(set(us)) > 1 else None
    rs_ = spearman([x["units0"] for x in rs], [x["live_fps"] for x in rs]) if len(set(us)) > 1 else None
    print("  %-22s n=%2d units0档=%-22s live %6.2f..%6.2f ρ_P=%s ρ_S=%s" % (
        h[:22], len(rs), str(us), ls[0], ls[-1],
        "%+.4f" % rp if rp is not None else "零方差",
        "%+.4f" % rs_ if rs_ is not None else "零方差"))

print("\n" + "=" * 104)
print("3) 快慢 × harness 版本 × 协议(measure-start-frame) 列联（带内 1180-1360，严格窗）")
print("=" * 104)
B = [r for r in P3 if 1180 <= r["units0"] <= 1360]
tab = defaultdict(lambda: [0, 0, set(), set(), set()])
for r in B:
    k = "FAST(>=28)" if r["live_fps"] >= 28 else ("SLOW(<20)" if r["live_fps"] < 20 else "MID")
    tab[hlabel(r)][0 if k == "FAST(>=28)" else 1] += 1
    tab[hlabel(r)][2].add(k)
    tab[hlabel(r)][3].add(SF.get(r["dir"], "?"))
    tab[hlabel(r)][4].add(r["ts"][:10])
for h, v in sorted(tab.items(), key=lambda x: min(y["ts"] for y in B if hlabel(y) == x[0])):
    print("  %-22s fast=%d slow/mid=%d  态=%s sf=%s 日期=%s" % (
        h[:22], v[0], v[1], sorted(v[2]), sorted(v[3]), sorted(v[4])))
a = sum(1 for r in B if hlabel(r) == "38244d2907e7f7fa" and r["live_fps"] >= 28)
b = sum(1 for r in B if hlabel(r) == "38244d2907e7f7fa" and r["live_fps"] < 28)
c = sum(1 for r in B if hlabel(r) != "38244d2907e7f7fa" and r["live_fps"] >= 28)
d2 = sum(1 for r in B if hlabel(r) != "38244d2907e7f7fa" and r["live_fps"] < 28)
print("  ⇒ v4 vs 非v4 × 快 vs 慢 = [[%d,%d],[%d,%d]] 双侧 Fisher p=%.3g" % (a, b, c, d2, fisher(a, b, c, d2)))
a2 = sum(1 for r in B if SF.get(r["dir"]) == "800" and r["live_fps"] >= 28)
b2 = sum(1 for r in B if SF.get(r["dir"]) == "800" and r["live_fps"] < 28)
c2 = sum(1 for r in B if SF.get(r["dir"]) != "800" and r["live_fps"] >= 28)
d3 = sum(1 for r in B if SF.get(r["dir"]) != "800" and r["live_fps"] < 28)
print("  ⇒ 协议 sf=800 vs sf!=800 × 快 vs 慢 = [[%d,%d],[%d,%d]] Fisher p=%.3g" % (
    a2, b2, c2, d3, fisher(a2, b2, c2, d3)))
print("  ⇒ 带内 fast 组 units0 值 %s ；slow 组 units0 值 %s" % (
    sorted(set(int(r["units0"]) for r in B if r["live_fps"] >= 28)),
    sorted(set(int(r["units0"]) for r in B if r["live_fps"] < 28))))

print("\n" + "=" * 104)
print("4) 全库（不限带内）版本内是否同时出现过 fast 与 slow —— 判共线性")
print("=" * 104)
for h, rs in sorted(hv.items(), key=lambda x: min(y["ts"] for y in x[1])):
    f = sum(1 for x in rs if x["live_fps"] >= 28)
    s = sum(1 for x in rs if x["live_fps"] < 20)
    print("  %-22s n=%2d fast=%2d slow=%2d  ⇒ %s   负载档 %s" % (
        h[:22], len(rs), f, s, "两态皆有" if f and s else "单态",
        sorted(set(int(x["units0"]) for x in rs))))

print("\n" + "=" * 104)
print("5) §544 点名对照的原文数字（逐窗自己算）")
print("=" * 104)
for d, lab in (("l3_1101v4d", "11-01 16:48"), ("l3_1101v4e", "11-03 11:20"),
               ("l1c_20261021", "10-21 19:03"), ("l3_20261021", "10-21 21:10"),
               ("l3_20261031hb", "10-31 20:15")):
    rs = sorted([r for r in rows if r["dir"] == d], key=lambda x: int(x["window"]))
    inb = 1180 <= rs[0]["units0"] <= 1360
    print("  %-16s %-12s units0=%-5d ∈带内?%s map=%-12s %-22s live=%s" % (
        d, lab, int(rs[0]["units0"]), "是" if inb else "★否", (rs[0]["map_sha256"] or "")[:12],
        hlabel(rs[0])[:22],
        " ".join("%.2f" % r["live_fps"] for r in rs if r["live_fps"])))
print("  ⇒ 「10-21 19:03 的 9.2fps」= l1c_20261021 units0=881，在 L1 图 0add791d 上，")
print("     与 11-01/11-03 的 L3 图 f3bb0a4e + units0 1189-1225 不同图不同负载不同版本。")
