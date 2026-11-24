# -*- coding: utf8 -*-
"""RC-A：带内 units0∈[1180,1360] 严格窗 × harness 版本 × 协议，快慢列联 + 双侧 Fisher。
窗级与趟级各算一遍（趟级避免 3 窗当 3 独立样本）。Fisher 自己实现（超几何）。
"""
import csv, os, statistics
from collections import defaultdict

OUT = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(OUT, "rc_census.csv"), encoding="utf-8")))
for r in rows:
    for k in ("units0", "live", "pre_fps15", "span_s", "gap_s", "c_units", "f0", "f1"):
        try:
            r[k] = float(r[k])
        except (TypeError, ValueError):
            r[k] = None
    r["argv"] = os.path.basename(r["argv"]) if r["argv"] else None

def lab(r):
    if r["sha16"]:
        return r["sha16"]
    if r["argv"] and "harness3" in r["argv"]:
        return "harness3(sha未记录)"
    return "UNKNOWN"

S = [r for r in rows if r["base_tag"] == "mirror" and r["verdict"] == "ok"
     and r["span_s"] == 25.0 and r["live"] and r["live"] > 0 and r["units0"] is not None]
B = [r for r in S if 1180 <= r["units0"] <= 1360]
print("严格窗 n=%d ；带内 n=%d 窗 / %d 趟" % (len(S), len(B), len(set(r["dir"] for r in B))))
print("\n带内窗分布（live 升序，看快慢天然间隙）：")
for r in sorted(B, key=lambda x: x["live"]):
    print("   %6.2f  %-16s %-22s sf=%-8s units0=%-5d %s" % (
        r["live"], r["dir"], lab(r), r["sf"] or "default", r["units0"], r["ts"][:16]))
lv = sorted(r["live"] for r in B)
gaps = sorted(((lv[i+1]-lv[i], lv[i], lv[i+1]) for i in range(len(lv)-1)), reverse=True)
print("  最大间隙：", ["%.2f (%.2f->%.2f)" % g for g in gaps[:3]])

def fisher(a, b, c, d):
    """双侧 Fisher 精确检验：累加所有 P(table)<=P(observed) 的超几何概率。"""
    from math import comb
    n, r1, c1 = a+b+c+d, a+b, a+c
    def P(x):
        if comb(r1, x) == 0 or comb(n-r1, c1-x) == 0:
            return 0.0
        return comb(r1, x)*comb(n-r1, c1-x)/comb(n, c1)
    po = P(a)
    return sum(P(x) for x in range(max(0, c1-(n-r1)), min(r1, c1)+1) if P(x) <= po*(1+1e-12)), po

def tab(rows_, groupfn, cut=28.0):
    t = defaultdict(lambda: [0, 0])
    for r in rows_:
        t[groupfn(r)][0 if r["live"] >= cut else 1] += 1
    return dict(t)

print("\n== 窗级列联（fast=live>=%.0f）==" % 28)
for k, v in sorted(tab(B, lab).items()):
    print("   %-24s fast=%d slow=%d" % (k, v[0], v[1]))
for gname, gfn in (("v4(38244d29) vs 非v4", lambda r: "v4" if r["sha16"] == "38244d2907e7f7fa" else "nonv4"),
                   ("sf=800 vs sf!=800", lambda r: "800" if r["sf"] == "800" else "not800"),
                   ("11-01之后 vs 之前(时段)", lambda r: "late" if (r["ts"] or "") >= "2026-11-01T12" else "early")):
    t = tab(B, gfn)
    k1, k2 = sorted(t)
    a, b = t[k1]; c, d = t[k2]
    p, po = fisher(a, b, c, d)
    print("   %-26s [[%d,%d],[%d,%d]] 双侧Fisher p=%.4g (观测表p=%.4g)" % (gname, a, b, c, d, p, po))

print("\n== 趟级（每趟取 live 中位，n=%d 趟）==" % len(set(r["dir"] for r in B)))
trips = defaultdict(list)
for r in B:
    trips[r["dir"]].append(r)
TB = []
for d, rs in trips.items():
    m = statistics.median(x["live"] for x in rs)
    TB.append(dict(dir=d, live=m, sha16=rs[0]["sha16"], sf=rs[0]["sf"], units0=rs[0]["units0"],
                   ts=rs[0]["ts"], n=len(rs), argv=rs[0]["argv"], f0=rs[0]["f0"]))
for t in sorted(TB, key=lambda x: x["live"]):
    print("   %6.2f (n=%d窗) %-16s %-22s sf=%-8s units0=%-5d %s" % (
        t["live"], t["n"], t["dir"], lab(t), t["sf"] or "default", t["units0"], t["ts"][:16]))
for gname, gfn in (("v4 vs 非v4", lambda r: "v4" if r["sha16"] == "38244d2907e7f7fa" else "nonv4"),
                   ("sf=800 vs !=800", lambda r: "800" if r["sf"] == "800" else "not800")):
    t = tab(TB, gfn)
    k1, k2 = sorted(t)
    a, b = t[k1]; c, d = t[k2]
    p, _ = fisher(a, b, c, d)
    print("   %-20s [[%d,%d],[%d,%d]] 双侧Fisher p=%.4g" % (gname, a, b, c, d, p))

print("\n带内 fast units0=%s  slow units0=%s" % (
    sorted(set(int(r["units0"]) for r in B if r["live"] >= 28)),
    sorted(set(int(r["units0"]) for r in B if r["live"] < 28))))
f = [r for r in B if r["live"] >= 28]; sl = [r for r in B if r["live"] < 28]
print("fast 首沿帧 %s 首窗首沿 %s" % (sorted(set(int(r["f0"]) for r in f if r["f0"])), ""))
print("slow 首沿帧 %s" % sorted(set(int(r["f0"]) for r in sl if r["f0"])))
