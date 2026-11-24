# -*- coding: utf-8 -*-
"""V2 终判：负载-版本可识别性 + 仅用负载能否解释全部窗（含趟内漂移）。

A) 各 harness 版本的窗内均值负载 (c_units) 取值区间是否互不重叠 ⇒ 版本效应与负载效应不可分
B) 单一地图(f3bb0a4e) 上，把全部窗（跨 5 个版本、4 个日期）按 c_units 排，看 live 是否单调
C) 用「同图同版本」的趟内漂移检验负载模型：窗内 c_units 降 ⇒ live 升？
D) 控制负载后的时代残差：同图 ±80 c_units 的跨日期/跨版本配对
"""
import csv
import itertools
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


rows = []
with open(os.path.join(OUT, "census.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["base_tag"] != "mirror":
            continue
        for k in ("live_fps", "units0", "pre_fps15", "span_s"):
            r[k] = ff(r[k])
        r["ts"] = r["fields_ts_first"] or ""
        rows.append(r)

for r in rows:
    p = os.path.join(TRIPS, r["dir"], "measure_w%s.json" % r["window"]) if r["dir"] != "." \
        else os.path.join(TRIPS, "measure_w%s.json" % r["window"])
    if not os.path.exists(p):
        continue
    j = json.load(open(p, encoding="utf-8"))
    cs = j.get("counters") or []
    def mean(k):
        vals = [c.get(k) for c in cs if isinstance(c.get(k), int)]
        return sum(vals) / len(vals) if vals else None
    r["c_units"] = mean("units")
    r["c_inf"] = mean("infantry")
    r["c_techno"] = mean("techno")


def hlabel(r):
    if r["harness_sha16"]:
        return r["harness_sha16"]
    ap = r["argv_harness"] or r["harness_path"]
    return "harness3" if "harness3" in os.path.basename(ap or "") else ("name:" + os.path.basename(ap) if ap else "UNKNOWN")


strict = [r for r in rows if r["verdict"] == "ok" and r["span_s"] == 25.0
          and r["live_fps"] and r["live_fps"] > 0 and r["c_units"] is not None]
L3 = [r for r in strict if (r["map_sha256"] or "").startswith("f3bb0a4e")]

print("=" * 110)
print("AA. 各版本的窗内均值负载 c_units 取值区间（单张 L3 图 f3bb0a4e 上）")
print("=" * 110)
hv = defaultdict(list)
for r in L3:
    hv[hlabel(r)].append(r)
ivs = {}
for h, rs in hv.items():
    us = [x["c_units"] for x in rs]
    ivs[h] = (min(us), max(us))
    print("  %-24s 日期 %s  n_窗=%2d  c_units %.1f..%.1f  live %.2f..%.2f" % (
        h, ",".join(sorted(set(x["ts"][:10] for x in rs))), len(rs), min(us), max(us),
        min(x["live_fps"] for x in rs), max(x["live_fps"] for x in rs)))
ks = sorted(ivs, key=lambda k: ivs[k][0])
print("\n  按负载区间排序：")
for k in ks:
    print("     %-24s c_units %.1f..%.1f  live %s" % (
        k, ivs[k][0], ivs[k][1],
        "%.2f..%.2f" % (min(x["live_fps"] for x in hv[k]), max(x["live_fps"] for x in hv[k]))))
overlaps = []
for a, b in itertools.combinations(ks, 2):
    lo = max(ivs[a][0], ivs[b][0])
    hi = min(ivs[a][1], ivs[b][1])
    if lo <= hi:
        overlaps.append((a, b, round(lo, 1), round(hi, 1)))
print("  ⇒ 版本间 c_units 区间重叠对：%s" % (overlaps if overlaps else "无（版本与负载完全不可分）"))
gap_pairs = []
for i in range(len(ks) - 1):
    a, b = ks[i], ks[i + 1]
    gap_pairs.append((a, round(ivs[a][1], 1), b, round(ivs[b][0], 1), round(ivs[b][0] - ivs[a][1], 1)))
print("  相邻版本负载间隙：%s" % gap_pairs)

print("\n" + "=" * 110)
print("AB. L3 图上全部窗（跨 5 版本 / 4 日期）按 c_units 升序 —— 看 live 是否单调")
print("=" * 110)
for r in sorted(L3, key=lambda x: x["c_units"]):
    ms = 1000.0 / r["live_fps"]
    print("   c_units=%-7.1f inf=%-6.1f live=%6.2f 帧时=%6.2fms %-18s %-10s %-22s" % (
        r["c_units"], r["c_inf"], r["live_fps"], ms, r["dir"][:18], r["ts"][:10], hlabel(r)[:22]))
print("  单调性检查（趟级，c_units 升序 vs live 降序）：")
tl = {}
for d in set(r["dir"] for r in L3):
    rs = [x for x in L3 if x["dir"] == d]
    tl[d] = (statistics.mean([x["c_units"] for x in rs]), statistics.median([x["live_fps"] for x in rs]),
            rs[0]["ts"][:10], hlabel(rs[0]))
seq = sorted(tl.values())
live_seq = [v[1] for v in seq]
inv = sum(1 for i in range(len(live_seq)) for j in range(i + 1, len(live_seq)) if live_seq[i] < live_seq[j])
print("   趟级 %d 个；按 c_units 升序后 live 逆序对数 = %d / %d" % (
    len(seq), inv, len(seq) * (len(seq) - 1) // 2))
print("   ρ_P(c_units, live) 窗级 L3 = %s  ρ_S = %s  (n=%d)" % (
    round(pearson([r["c_units"] for r in L3], [r["live_fps"] for r in L3]), 4),
    round(spearman([r["c_units"] for r in L3], [r["live_fps"] for r in L3]), 4), len(L3)))
print("   ρ_P(c_units, 帧时ms) = %s (n=%d)" % (
    round(pearson([r["c_units"] for r in L3], [1000 / r["live_fps"] for r in L3]), 4), len(L3)))
for v in seq:
    print("      c_units=%-7.1f live=%6.2f %-10s %s" % (v[0], v[1], v[2], v[3][:22]))

print("\n" + "=" * 110)
print("AC. 趟内漂移 vs 负载：同趟同版本同图，窗序 c_units 下降时 live 是否上升")
print("=" * 110)
bytrip = defaultdict(list)
for r in L3:
    bytrip[r["dir"]].append(r)
agree = disagree = 0
for d, rs in sorted(bytrip.items()):
    rs = sorted(rs, key=lambda x: int(x["window"]))
    if len(rs) < 2:
        continue
    line = []
    for x in rs:
        line.append("w%s cu=%.0f live=%.2f" % (x["window"], x["c_units"], x["live_fps"]))
    # 单调一致度
    cs = [x["c_units"] for x in rs]
    ls = [x["live_fps"] for x in rs]
    dd = sum(1 for i in range(len(rs) - 1) if cs[i + 1] < cs[i])
    ll = sum(1 for i in range(len(rs) - 1) if ls[i + 1] > ls[i])
    ok = dd == ll
    agree += 1 if ok else 0
    disagree += 0 if ok else 1
    print("   %-18s %-22s %s  负载降 %d 步 / live 升 %d 步 ⇒ %s" % (
        d, hlabel(rs[0])[:22], " | ".join(line), dd, ll, "一致" if ok else "不一致"))
print("   一致 %d 趟 / 不一致 %d 趟" % (agree, disagree))
print("   窗级 ρ_P(c_units, live) 同趟去均值后残差：")
resid_x, resid_y = [], []
for d, rs in bytrip.items():
    mx = statistics.mean([x["c_units"] for x in rs])
    my = statistics.mean([x["live_fps"] for x in rs])
    for x in rs:
        resid_x.append(x["c_units"] - mx)
        resid_y.append(x["live_fps"] - my)
print("     组内(去趟均值) ρ_P = %s (n=%d)" % (round(pearson(resid_x, resid_y), 4), len(resid_x)))

print("\n" + "=" * 110)
print("AD. 控制负载（同 L3 图，窗内 c_units ±80）后的跨日期/跨版本配对")
print("=" * 110)
found = []
for a, b in itertools.combinations(sorted(tl), 2):
    A, B = tl[a], tl[b]
    if abs(A[0] - B[0]) <= 80 and (a, b) and (A[3] != B[3] or A[2] != B[2]):
        found.append((max(A[1], B[1]) / min(A[1], B[1]), a, b, A, B))
found.sort(reverse=True)
if not found:
    print("   无配对 ⇒ 该库无法给出「同负载跨时代」的任何一对干净对照")
for ratio, a, b, A, B in found:
    print("   %.2fx  %-18s c=%.0f live=%6.2f %s %s   vs  %-18s c=%.0f live=%6.2f %s %s" % (
        ratio, a, A[0], A[1], A[2], A[3][:12], b, B[0], B[1], B[2], B[3][:12]))

print("\n" + "=" * 110)
print("AE. L1 图 0add791d 同法（732/702 快 vs 866-881 慢）")
print("=" * 110)
L1 = [r for r in strict if (r["map_sha256"] or "").startswith("0add791d")]
t1 = {}
for d in set(r["dir"] for r in L1):
    rs = [x for x in L1 if x["dir"] == d]
    t1[d] = (statistics.mean([x["c_units"] for x in rs]), statistics.median([x["live_fps"] for x in rs]),
             rs[0]["ts"][:10], hlabel(rs[0]))
for d, v in sorted(t1.items(), key=lambda x: x[1][0]):
    print("   c_units=%-7.1f live=%6.2f %-10s %-24s %s" % (v[0], v[1], v[2], v[3][:24], d))
print("   ρ_P(c_units, live) L1 窗级 = %s ρ_S = %s (n=%d)" % (
    round(pearson([r["c_units"] for r in L1], [r["live_fps"] for r in L1]), 4),
    round(spearman([r["c_units"] for r in L1], [r["live_fps"] for r in L1]), 4), len(L1)))
