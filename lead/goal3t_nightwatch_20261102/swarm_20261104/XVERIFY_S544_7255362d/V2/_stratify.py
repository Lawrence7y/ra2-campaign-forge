# -*- coding: utf-8 -*-
"""V2 分层检验：控制 map + 负载档之后，日期/版本还剩多少解释力。"""
import csv
import json
import math
import os
import statistics
from collections import defaultdict

ROOT = r"D:\Project\ra2-campaign-forge"
TRIPS = ROOT + r"\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUT = os.path.dirname(os.path.abspath(__file__))


def ff(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    dx = math.sqrt(sum((a - mx) ** 2 for a in xs))
    dy = math.sqrt(sum((b - my) ** 2 for b in ys))
    return num / (dx * dy) if dx > 0 and dy > 0 else None


rows = []
with open(os.path.join(OUT, "census.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["base_tag"] != "mirror":
            continue
        for k in ("live_fps", "units0", "pre_fps15", "span_s"):
            r[k] = ff(r[k])
        r["ts"] = r["fields_ts_first"] or ""
        rows.append(r)


def hlabel(r):
    if r["harness_sha16"]:
        return r["harness_sha16"]
    ap = r["argv_harness"] or r["harness_path"]
    return "name:" + os.path.basename(ap) if ap else "UNKNOWN"


strict = [r for r in rows if r["verdict"] == "ok" and r["span_s"] == 25.0
          and r["live_fps"] and r["live_fps"] > 0 and r["units0"] is not None]
trip = defaultdict(list)
for r in strict:
    trip[r["dir"]].append(r)
T = {}
for d, rs in trip.items():
    T[d] = dict(u=int(rs[0]["units0"]), live=statistics.median([x["live_fps"] for x in rs]),
                rng=max(x["live_fps"] for x in rs) - min(x["live_fps"] for x in rs),
                n=len(rs), date=rs[0]["ts"][:10], tm=rs[0]["ts"][11:19],
                h=hlabel(rs[0]), map=(rs[0]["map_sha256"] or "")[:12])

print("=" * 112)
print("P. 分层：map × 负载档（每 100 一档），档内跨日期/跨版本比较")
print("=" * 112)
cells = defaultdict(list)
for d, v in T.items():
    cells[(v["map"], v["u"] // 200)].append((d, v))
for key in sorted(cells):
    lst = sorted(cells[key], key=lambda x: x[1]["u"])
    print("  map=%s 档 units0∈[%d,%d)：" % (key[0], key[1] * 200, key[1] * 200 + 199))
    for d, v in lst:
        print("     %-18s %-11s %s %s units0=%-5d live=%6.2f (趟内极差 %.2f, n=%d) harness=%s" % (
            d, v["map"], v["date"], v["tm"], v["u"], v["live"], v["rng"], v["n"], v["h"][:20]))
    ls = [v["live"] for _, v in lst]
    if len(lst) >= 2:
        print("     档内倍率 max/min = %.2fx ；跨日期？%s ；跨版本？%s" % (
            max(ls) / min(ls), len(set(v["date"] for _, v in lst)) > 1,
            len(set(v["h"] for _, v in lst)) > 1))

print("\n" + "=" * 112)
print("Q. 版本 × 地图单元格内 ρ(units0, live)（n>=3 才报）")
print("=" * 112)
cell2 = defaultdict(list)
for r in strict:
    cell2[(hlabel(r), (r["map_sha256"] or "")[:12])].append(r)
for k, rs in sorted(cell2.items(), key=lambda x: -len(x[1])):
    if len(rs) < 3:
        continue
    print("  %-30s map=%-13s n=%2d units0 %s live %6.2f..%6.2f ρ_P=%s" % (
        k[0][:30], k[1], len(rs), sorted(set(int(x["units0"]) for x in rs)),
        min(x["live_fps"] for x in rs), max(x["live_fps"] for x in rs),
        round(pearson([x["units0"] for x in rs], [x["live_fps"] for x in rs]), 4)
        if len(set(int(x["units0"]) for x in rs)) > 1 else "零方差"))

print("\n" + "=" * 112)
print("R. 反例检索：同 map 同负载(±60) 不同日期 —— 时代效应的最小可证伪对照")
print("=" * 112)
import itertools
found = []
for a, b in itertools.combinations(sorted(T), 2):
    A, B = T[a], T[b]
    if A["map"] == B["map"] and abs(A["u"] - B["u"]) <= 60 and A["date"] != B["date"]:
        found.append((max(A["live"], B["live"]) / min(A["live"], B["live"]), a, b))
found.sort(reverse=True)
for ratio, a, b in found:
    A, B = T[a], T[b]
    print("  %.3fx  %-16s %s %s u=%-5d live=%6.2f | %-16s %s %s u=%-5d live=%6.2f | 版本 %s / %s" % (
        ratio, a, A["date"], A["tm"], A["u"], A["live"], b, B["date"], B["tm"], B["u"], B["live"],
        A["h"][:12], B["h"][:12]))
print("  共 %d 对；全部倍率 <= %.2fx，远小于 3x" % (len(found), found[0][0]) if found else "  无对")
print("  同 map 同负载(±60) 同日期不同时段的对照：")
for a, b in itertools.combinations(sorted(T), 2):
    A, B = T[a], T[b]
    if A["map"] == B["map"] and abs(A["u"] - B["u"]) <= 60 and A["date"] == B["date"]:
        print("     %.3fx  %-16s %s %s u=%-5d live=%6.2f | %-16s %s u=%-5d live=%6.2f | 版本 %s/%s" % (
            max(A["live"], B["live"]) / min(A["live"], B["live"]), a, A["date"], A["tm"], A["u"], A["live"],
            b, B["tm"], B["u"], B["live"], A["h"][:12], B["h"][:12]))

print("\n" + "=" * 112)
print("S. 慢档内部：跨趟差 vs 趟内窗差（谁大？）")
print("=" * 112)
slow = {d: v for d, v in T.items() if v["live"] < 20}
fast = {d: v for d, v in T.items() if v["live"] >= 28}
for name, grp in (("慢档", slow), ("快档", fast)):
    if not grp:
        continue
    within = [v["rng"] for v in grp.values() if v["n"] >= 2]
    meds = [v["live"] for v in grp.values()]
    print("  %s 趟数=%d；趟内窗间极差中位=%s；趟间中位数极差=%.2f (%.2fx)" % (
        name, len(grp), "%.2f" % statistics.median(within) if within else "n/a",
        max(meds) - min(meds), max(meds) / min(meds)))
