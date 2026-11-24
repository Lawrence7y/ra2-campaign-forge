# -*- coding: utf8 -*-
"""RC-F：版本内 ρ(units0,live) 复核 + 去趟均值后的组内 ρ + 各版本负载区间 + 快慢组首沿帧口径。"""
import csv, os, statistics
from collections import defaultdict

OUT = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(OUT, "rc_census.csv"), encoding="utf-8")))
for r in rows:
    for k in ("units0", "live", "span_s", "pre_fps15", "c_units", "f0"):
        try:
            r[k] = float(r[k])
        except (TypeError, ValueError):
            r[k] = None
    r["argv"] = os.path.basename(r["argv"]) if r["argv"] else None
M = [r for r in rows if r["base_tag"] == "mirror"]

def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs)/n, sum(ys)/n
    dx = sum((a-mx)**2 for a in xs) ** .5
    dy = sum((b-my)**2 for b in ys) ** .5
    return None if dx == 0 or dy == 0 else sum((a-mx)*(b-my) for a, b in zip(xs, ys))/(dx*dy)

def lab(r):
    if r["sha16"]:
        return r["sha16"]
    if r["argv"] and "harness3" in r["argv"]:
        return "harness3(sha未记录)"
    return "UNKNOWN(无_launch_result)"

P3 = [r for r in M if r["verdict"] == "ok" and r["span_s"] == 25.0 and r["live"] and r["live"] > 0
      and r["units0"] is not None]
print("== 1) 版本内 ρ(units0, live)，严格窗池 n=%d ==" % len(P3))
by = defaultdict(list)
for r in P3:
    by[lab(r)].append(r)
for k, v in sorted(by.items(), key=lambda x: min(y["ts"] or "" for y in x[1])):
    us = sorted(set(int(x["units0"]) for x in v))
    rp = pearson([x["units0"] for x in v], [x["live"] for x in v])
    print("  %-24s n=%2d units0档=%-28s live %6.2f..%6.2f ρ_P=%s 快=%d 慢=%d" % (
        k, len(v), str(us)[:28], min(x["live"] for x in v), max(x["live"] for x in v),
        "%+.4f" % rp if rp is not None else "零方差",
        sum(1 for x in v if x["live"] >= 28), sum(1 for x in v if x["live"] < 20)))

print("\n== 2) L3 图去趟均值后的组内 ρ(c_units, live) ==")
L3 = [r for r in P3 if (r["map_sha256"] or "").startswith("f3bb0a4e") and r["c_units"]]
cent = []
for d, rs in defaultdict(list, {g["dir"]: [] for g in L3}).items():
    pass
g = defaultdict(list)
for r in L3:
    g[r["dir"]].append(r)
for d, rs in g.items():
    mc = statistics.median(x["c_units"] for x in rs)
    ml = statistics.median(x["live"] for x in rs)
    cent.append((mc, ml, d, len(rs)))
print("  趟均值 (c_units, live)：")
for mc, ml, d, n in sorted(cent):
    print("     c_u=%7.1f live=%6.2f  %-16s n=%d" % (mc, ml, d, n))
print("  趟均值级 ρ_P(c_units,live) = %+.4f (n=%d)" % (
    pearson([c[0] for c in cent], [c[1] for c in cent]), len(cent)))
w = []
for d, rs in g.items():
    mc = statistics.median(x["c_units"] for x in rs)
    ml = statistics.median(x["live"] for x in rs)
    for r in rs:
        w.append((r["c_units"]-mc, r["live"]-ml))
if len(w) >= 3:
    print("  去均值（组内残差）ρ_P(c_units,live) = %+.4f (n=%d 窗, %d 趟)" % (
        pearson([a for a, b in w], [b for a, b in w]), len(w), len(g)))
print("  组内：负载降 & live 同向降的趟数 = %d / %d" % (
    sum(1 for d, rs in g.items() if len(rs) >= 2 and
        (max(x["c_units"] for x in rs) > min(x["c_units"] for x in rs)) and
        ((max(rs, key=lambda x: x["c_units"])["live"] >= min(rs, key=lambda x: x["c_units"])["live"]))), len(g)))

print("\n== 3) 各版本在 L3 上的 c_units 区间（可识别性）==")
bl = defaultdict(list)
for r in L3:
    bl[lab(r)].append(r["c_units"])
for k, v in sorted(bl.items()):
    print("  %-24s c_units %.0f..%.0f (n=%d)" % (k, min(v), max(v), len(v)))

print("\n== 4) 快慢组 w0 首沿帧口径（报告称 fast 869-925 / slow 387-454）==")
B = [r for r in P3 if 1180 <= r["units0"] <= 1360]
for cut in (28.0,):
    f0f = sorted(int(x["f0"]) for x in B if x["live"] >= cut and x["window"] == "0")
    f0s = sorted(int(x["f0"]) for x in B if x["live"] < cut and x["window"] == "0")
    print("  fast(>=%.0f) w0 f0=%s  slow w0 f0=%s" % (cut, f0f, f0s))
    print("  全部窗（不分窗序）fast f0=%s slow f0=%s" % (
        sorted(set(int(x["f0"]) for x in B if x["live"] >= cut)),
        sorted(set(int(x["f0"]) for x in B if x["live"] < cut))))
    print("  v4c(1229) 三窗：%s" % [(x["window"], "%.2f" % x["live"], int(x["f0"]), "%.0f" % x["c_units"])
          for x in sorted([y for y in B if y["dir"] == "l3_1101v4c"], key=lambda z: int(z["window"]))])
