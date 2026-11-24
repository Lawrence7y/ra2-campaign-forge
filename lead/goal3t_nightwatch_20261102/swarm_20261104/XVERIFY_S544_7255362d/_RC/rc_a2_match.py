# -*- coding: utf8 -*-
"""RC-A2：决定性判据复算 —— 同一张 L3 图 + 窗内均值负载 ±40 的配对倍率，同版本 vs 跨版本。
窗级与趟级各算一次。
"""
import csv, itertools, os, statistics
from collections import defaultdict

OUT = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(OUT, "rc_census.csv"), encoding="utf-8")))
for r in rows:
    for k in ("units0", "live", "pre_fps15", "span_s", "gap_s", "c_units", "c_inf"):
        try:
            r[k] = float(r[k])
        except (TypeError, ValueError):
            r[k] = None
    r["argv"] = os.path.basename(r["argv"]) if r["argv"] else None

def lab(r):
    if r["sha16"]:
        return r["sha16"]
    if r["argv"] and "harness3" in r["argv"]:
        return "harness3"
    return "UNKNOWN"

L3w = [r for r in rows if r["base_tag"] == "mirror" and r["verdict"] == "ok" and r["span_s"] == 25.0
       and r["live"] and r["live"] > 0 and r["c_units"] is not None
       and (r["map_sha256"] or "").startswith("f3bb0a4e")]
print("L3 严格窗 n=%d，趟 n=%d" % (len(L3w), len(set(r["dir"] for r in L3w))))
print("各版本在 L3 上的 c_units 区间：")
by = defaultdict(list)
for r in L3w:
    by[lab(r)].append(r)
for k, v in sorted(by.items(), key=lambda x: min(y["ts"] for y in x[1])):
    print("   %-24s n=%2d c_units %.0f..%.0f  live %.2f..%.2f  趟 %s" % (
        k, len(v), min(x["c_units"] for x in v), max(x["c_units"] for x in v),
        min(x["live"] for x in v), max(x["live"] for x in v), sorted(set(x["dir"] for x in v))))

for TOL in (40, 25, 60):
    same, cross = [], []
    for a, b in itertools.combinations(L3w, 2):
        if a["dir"] == b["dir"] or abs(a["c_units"] - b["c_units"]) > TOL:
            continue
        ratio = max(a["live"], b["live"]) / min(a["live"], b["live"])
        (same if lab(a) == lab(b) else cross).append((ratio, a, b))
    def summ(t):
        if not t:
            return "n=0"
        rs = [x[0] for x in t]
        return "n=%2d 中位 %.2fx max %.2fx >3x对数=%d" % (
            len(t), statistics.median(rs), max(rs), sum(1 for x in rs if x > 3))
    print("\n[窗级] ±%d 同图：同版本 %s | 跨版本 %s" % (TOL, summ(same), summ(cross)))
    print("        跨版本 >3x 的对：")
    for ratio, a, b in sorted(cross, reverse=True):
        if ratio > 3:
            print("          %.2fx  %s(%s,c_u=%.0f,live=%.2f) vs %s(%s,c_u=%.0f,live=%.2f)" % (
                ratio, a["dir"], lab(a)[:8], a["c_units"], a["live"], b["dir"], lab(b)[:8], b["c_units"], b["live"]))
    print("        同版本最大 3 对：")
    for ratio, a, b in sorted(same, reverse=True)[:3]:
        print("          %.2fx  %s vs %s (live %.2f/%.2f)" % (ratio, a["dir"], b["dir"], a["live"], b["live"]))

# 趟级：每趟 c_units 与 live 取中位
T = {}
for r in L3w:
    T.setdefault(r["dir"], []).append(r)
TP = []
for d, rs in T.items():
    TP.append(dict(dir=d, live=statistics.median(x["live"] for x in rs),
                   c_units=statistics.median(x["c_units"] for x in rs), sha=lab(rs[0]),
                   ts=rs[0]["ts"], n=len(rs)))
print("\n== 趟级（L3 图，%d 趟）==" % len(TP))
for t in sorted(TP, key=lambda x: x["c_units"]):
    print("   %-16s %-24s n=%d c_units=%.0f live=%6.2f %s" % (
        t["dir"], t["sha"], t["n"], t["c_units"], t["live"], t["ts"][:16]))
for TOL in (40, 25):
    same, cross = [], []
    for a, b in itertools.combinations(TP, 2):
        if abs(a["c_units"] - b["c_units"]) > TOL:
            continue
        ratio = max(a["live"], b["live"]) / min(a["live"], b["live"])
        (same if a["sha"] == b["sha"] else cross).append(ratio)
    def summ(t):
        return ("n=%d 中位 %.2fx max %.2fx >3x=%d" % (len(t), statistics.median(t), max(t),
                                                       sum(1 for x in t if x > 3))) if t else "n=0"
    print("   ±%d 同版本 %s | 跨版本 %s" % (TOL, summ(same), summ(cross)))
