# -*- coding: utf-8 -*-
"""V2 终判：同 map 同负载跨日期配对、负载断崖、机器状态(uptime)、ρ(pre15,live) 池敏感性。"""
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


rows = []
with open(os.path.join(OUT, "census.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["base_tag"] != "mirror":
            continue
        for k in ("live_fps", "units0", "pre_fps15", "span_s", "t_abs0", "t_first_edge"):
            r[k] = ff(r[k])
        r["ts"] = r["fields_ts_first"] or ""
        rows.append(r)

# 窗内真实负载 + uptime
for r in rows:
    p = os.path.join(TRIPS, r["dir"], "measure_w%s.json" % r["window"]) if r["dir"] != "." \
        else os.path.join(TRIPS, "measure_w%s.json" % r["window"])
    if os.path.exists(p):
        j = json.load(open(p, encoding="utf-8"))
        cs = j.get("counters") or []
        u = [c.get("units") for c in cs if isinstance(c.get("units"), int)]
        t = [c.get("techno") for c in cs if isinstance(c.get("techno"), int)]
        inf = [c.get("infantry") for c in cs if isinstance(c.get("infantry"), int)]
        r["units_mean"] = sum(u) / len(u) if u else None
        r["techno_mean"] = sum(t) / len(t) if t else None
        r["inf_mean"] = sum(inf) / len(inf) if inf else None
        r["uptime_h"] = (r["t_first_edge"] / 3600.0) if r["t_first_edge"] else None
        r["t_abs0_dt"] = None
        if r["t_abs0"]:
            import datetime
            r["t_abs0_dt"] = datetime.datetime.utcfromtimestamp(r["t_abs0"]) + datetime.timedelta(hours=8)


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

print("=" * 112)
print("G. 同 map、|Δunits0|<=100、跨日期的趟级配对（这是唯一能干净分离「时代」的对照）")
print("=" * 112)
info = {}
for d, rs in trip.items():
    info[d] = dict(u=rs[0]["units0"], live=statistics.median([x["live_fps"] for x in rs]),
                   date=rs[0]["ts"][:10], h=hlabel(rs[0]), map=(rs[0]["map_sha256"] or "")[:12],
                   um=statistics.mean([x["units_mean"] for x in rs if x["units_mean"]]))
pairs = []
for a, b in itertools.combinations(sorted(info), 2):
    A, B = info[a], info[b]
    if A["map"] == B["map"] and A["date"] != B["date"] and abs(A["u"] - B["u"]) <= 100:
        ratio = max(A["live"], B["live"]) / min(A["live"], B["live"])
        pairs.append((ratio, a, b, A, B))
pairs.sort(reverse=True)
if not pairs:
    print("  （无配对）")
for ratio, a, b, A, B in pairs:
    print("  比值 %.3fx  %s(units0=%d,live=%.2f,%s,%s) vs %s(units0=%d,live=%.2f,%s,%s)" % (
        ratio, a, A["u"], A["live"], A["date"], A["h"][:14], b, B["u"], B["live"], B["date"], B["h"][:14]))
print("  同 map 同负载带跨日期配对共 %d 对；最大跨日期倍率 = %s" % (
    len(pairs), round(pairs[0][0], 3) if pairs else "无"))

print("\n  同 map 同负载带跨日期 **且跨 harness 版本** 的配对：")
n_cross_ver = 0
for ratio, a, b, A, B in pairs:
    if A["h"] != B["h"]:
        n_cross_ver += 1
        print("     %-34s vs %-34s 倍率 %.3fx 版本 %s / %s" % (
            "%s u=%d l=%.2f %s" % (a, A["u"], A["live"], A["date"]),
            "%s u=%d l=%.2f %s" % (b, B["u"], B["live"], B["date"]), ratio, A["h"][:10], B["h"][:10]))
print("     共 %d 对；若这些对都落在 1.1x 内 ⇒ 版本/时段换了但速度没换" % n_cross_ver)

print("\n" + "=" * 112)
print("H. 负载-速度响应曲线（按 map 分组，趟级）：断崖在哪")
print("=" * 112)
bym = defaultdict(list)
for d, v in info.items():
    bym[v["map"]].append((v["u"], v["live"], d, v["date"], v["h"], v["um"]))
for m, lst in sorted(bym.items(), key=lambda x: -len(x[1])):
    print("  map=%s" % m)
    for u, live, d, date, h, um in sorted(lst):
        bar = "#" * int(live)
        print("     units0=%-6d units均=%-7.1f live=%6.2f %s  %-18s %-14s %s" % (
            u, um, live, date, d, h[:14], bar))

print("\n" + "=" * 112)
print("I. 机器状态：测量时的机器 uptime（perf_counter 起点）")
print("=" * 112)
seen = set()
for d, rs in sorted(trip.items(), key=lambda x: x[1][0]["ts"]):
    if d in seen:
        continue
    seen.add(d)
    r0 = sorted(rs, key=lambda x: int(x["window"]))[0]
    print("  %-19s %-18s live中位=%6.2f uptime_at_w0=%s h  abs0=%s units0=%d" % (
        r0["ts"][:19], d, statistics.median([x["live_fps"] for x in rs]),
        "%.2f" % r0["uptime_h"] if r0["uptime_h"] is not None else "-",
        r0["t_abs0_dt"].isoformat(timespec="seconds") if r0["t_abs0_dt"] else "-", int(r0["units0"])))
up = [info[d]["live"] for d in info]
upv = []
for d, rs in trip.items():
    r0 = rs[0]
    if r0["uptime_h"]:
        upv.append((r0["uptime_h"], statistics.median([x["live_fps"] for x in rs]), d))
print("  趟级 ρ_P(uptime_h, live) = %s (n=%d)" % (round(pearson([x[0] for x in upv], [x[1] for x in upv]), 4), len(upv)))
for u, l, d in sorted(upv):
    print("     uptime %7.2f h  live %6.2f  %s" % (u, l, d))

print("\n" + "=" * 112)
print("J. ρ(pre15, live) 池敏感性（§544 报 0.8925）")
print("=" * 112)
allc = [r for r in rows if r["live_fps"] and r["live_fps"] > 0 and r["pre_fps15"] is not None]
pools = {
    "全部可算窗(含 4s settle 伪窗)": allc,
    "同上加 units0 非空": [r for r in allc if r["units0"] is not None],
    "严格 25s 窗": [r for r in allc if r["verdict"] == "ok" and r["span_s"] == 25.0],
    "严格 25s 窗 ∧ units0 非空": [r for r in allc if r["verdict"] == "ok" and r["span_s"] == 25.0 and r["units0"] is not None],
    "严格 25s ∧ units0>0": [r for r in allc if r["verdict"] == "ok" and r["span_s"] == 25.0 and (r["units0"] or 0) > 0],
    "gate_ok=True 窗": [r for r in allc if r["gate_ok"] in ("True", "true", True)],
    "带内 1180-1360 严格窗": [r for r in allc if r["units0"] is not None and 1180 <= r["units0"] <= 1360
                             and r["verdict"] == "ok" and r["span_s"] == 25.0],
}
for name, pl in pools.items():
    rp = pearson([r["pre_fps15"] for r in pl], [r["live_fps"] for r in pl])
    print("  %-34s n=%2d ρ_P=%s" % (name, len(pl), round(rp, 4) if rp is not None else "None"))
tl = {d: statistics.median([x["live_fps"] for x in rs]) for d, rs in trip.items()}
tpd = {d: rs[0]["pre_fps15"] for d, rs in trip.items() if rs[0]["pre_fps15"] is not None}
ds = sorted(set(tl) & set(tpd))
print("  %-34s n=%2d ρ_P=%s" % ("趟级", len(ds), round(pearson([tpd[d] for d in ds], [tl[d] for d in ds]), 4)))

print("\n" + "=" * 112)
print("K. 同一趟内 pre15 vs 逐窗 live（同义反复的直接检验）")
print("=" * 112)
for d, rs in sorted(trip.items(), key=lambda x: x[1][0]["ts"]):
    if rs[0]["pre_fps15"] is None or len(rs) < 2:
        continue
    print("  %-18s pre15=%7.3f → 各窗 live %s (倍率 %.2fx)" % (
        d, rs[0]["pre_fps15"],
        " ".join("w%s:%.2f" % (r["window"], r["live_fps"]) for r in sorted(rs, key=lambda x: int(x["window"]))),
        max(r["live_fps"] for r in rs) / min(r["live_fps"] for r in rs)))
xs = [r["pre_fps15"] for r in strict if r["pre_fps15"] is not None]
ys = [r["live_fps"] for r in strict if r["pre_fps15"] is not None]
print("  窗级 pre15/live 比值：中位 %.3f，范围 %.3f..%.3f" % (
    statistics.median([a / b for a, b in zip(xs, ys) if b > 0]),
    min(a / b for a, b in zip(xs, ys) if b > 0), max(a / b for a, b in zip(xs, ys) if b > 0)))
