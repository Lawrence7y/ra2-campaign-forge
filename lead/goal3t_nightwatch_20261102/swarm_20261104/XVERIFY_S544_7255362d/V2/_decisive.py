# -*- coding: utf-8 -*-
"""V2 决定性检查：把「时代」拆开成 协议(测相位) × 版本 × 窗内实际负载。

1) 每趟用的 --h7-measure-start-frame / harness / 日期 三者是否共线
2) 窗内 counters.units 的均值（真实窗内负载）与 live_fps 的关系
3) 同 map 内 units0 升序排（看是不是断崖而非时段）
4) ρ(pre15,live) 在不同样本池下的敏感性（对 §544 的 0.8925 定位）
"""
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

# ---- 窗内真实负载：counters.units / techno / g 的均值 ----
winload = {}
for r in rows:
    p = os.path.join(TRIPS, r["dir"], "measure_w%s.json" % r["window"]) if r["dir"] != "." \
        else os.path.join(TRIPS, "measure_w%s.json" % r["window"])
    if not os.path.exists(p):
        continue
    j = json.load(open(p, encoding="utf-8"))
    cs = j.get("counters") or []
    u = [c.get("units") for c in cs if isinstance(c.get("units"), int)]
    t = [c.get("techno") for c in cs if isinstance(c.get("techno"), int)]
    g = [c.get("g") for c in cs if isinstance(c.get("g"), int)]
    if u:
        winload[(r["dir"], r["window"])] = {
            "units_mean": sum(u) / len(u), "units_min": min(u), "units_max": max(u),
            "techno_mean": sum(t) / len(t) if t else None,
            "g_mean": sum(g) / len(g) if g else None,
            "n_ctr": len(u), "units_end": u[-1]}

for r in rows:
    w = winload.get((r["dir"], r["window"]), {})
    r["units_mean"] = w.get("units_mean")
    r["units_end"] = w.get("units_end")
    r["techno_mean"] = w.get("techno_mean")
    r["g_mean"] = w.get("g_mean")


def hlabel(r):
    if r["harness_sha16"]:
        return r["harness_sha16"]
    ap = r["argv_harness"] or r["harness_path"]
    return "name:" + os.path.basename(ap) if ap else "UNKNOWN"


FLAGKEYS = ["--h7-measure-start-frame", "--h8-wait-trace", "--h8-wait-hz",
            "--h7-keep-rect-wait", "--fullscreen"]
flags = {}
for d in sorted(os.listdir(TRIPS)):
    p = os.path.join(TRIPS, d, "_launch_result.json")
    if not os.path.exists(p):
        continue
    argv = json.load(open(p, encoding="utf-8")).get("argv") or []
    fl = {}
    for i, a in enumerate(argv):
        if a in FLAGKEYS:
            nxt = argv[i + 1] if i + 1 < len(argv) and not str(argv[i + 1]).startswith("--") else "ON"
            fl[a] = nxt
    flags[d] = fl

strict = [r for r in rows if r["verdict"] == "ok" and r["span_s"] == 25.0
          and r["live_fps"] is not None and r["live_fps"] > 0 and r["units0"] is not None]

print("=" * 112)
print("A. 协议 × 版本 × 日期 共线表（严格窗池，按趟）")
print("=" * 112)
trip = defaultdict(list)
for r in strict:
    trip[r["dir"]].append(r)
print("%-19s %-16s %-22s %-6s %-8s %-12s %8s %8s %8s" % (
    "日期时间", "dir", "harness_sha16", "sf帧", "waittrc", "map", "units0", "units均", "live中位"))
for d, rs in sorted(trip.items(), key=lambda x: x[1][0]["ts"]):
    fl = flags.get(d, {})
    um = [x["units_mean"] for x in rs if x["units_mean"] is not None]
    print("%-19s %-16s %-22s %-6s %-8s %-12s %8d %8.1f %8.2f" % (
        rs[0]["ts"][:19], d[:16], hlabel(rs[0])[:22],
        str(fl.get("--h7-measure-start-frame", "default")),
        "Y" if "--h8-wait-trace" in fl else "n",
        (rs[0]["map_sha256"] or "-")[:12], int(rs[0]["units0"]),
        statistics.mean(um) if um else float("nan"),
        statistics.median([x["live_fps"] for x in rs])))

print("\n  ⇒ 组合 (harness, sf帧) 与日期：")
combo = defaultdict(set)
for d, rs in trip.items():
    combo[(hlabel(rs[0]), str(flags.get(d, {}).get("--h7-measure-start-frame", "default")))].add(rs[0]["ts"][:10])
for k, v in sorted(combo.items()):
    print("     %-24s sf=%-8s 日期 %s" % (k[0][:24], k[1], sorted(v)))

print("\n" + "=" * 112)
print("B. 同 map 内按 units0 升序 —— 看快慢是不是负载断崖")
print("=" * 112)
bym = defaultdict(list)
for r in strict:
    bym[(r["map_sha256"] or "-")[:12]].append(r)
for m, rs in sorted(bym.items(), key=lambda x: -len(x[1])):
    print("  map=%s  n_窗=%d" % (m, len(rs)))
    seen = set()
    for r in sorted(rs, key=lambda x: x["units0"]):
        key = (int(r["units0"]), r["dir"])
        if key in seen:
            continue
        seen.add(key)
        sub = [x for x in rs if x["dir"] == r["dir"]]
        print("     units0=%-6d live(趟中位)=%-7.2f %-16s %-20s sf=%-8s %s" % (
            r["units0"], statistics.median([x["live_fps"] for x in sub]), r["dir"][:16],
            hlabel(r)[:20], str(flags.get(r["dir"], {}).get("--h7-measure-start-frame", "default")),
            r["ts"][:10]))

print("\n" + "=" * 112)
print("C. 窗内真实负载（counters.units 均值）vs live_fps")
print("=" * 112)
pool2 = [r for r in strict if r["units_mean"] is not None]
for field in ("units0", "units_mean", "units_end", "techno_mean", "g_mean"):
    sub = [r for r in pool2 if r.get(field) is not None]
    rp = pearson([r[field] for r in sub], [r["live_fps"] for r in sub])
    print("  ρ_P(%-12s, live) = %s   n=%d  范围 %s..%s" % (
        field, round(rp, 4) if rp is not None else "None", len(sub),
        round(min(r[field] for r in sub), 1), round(max(r[field] for r in sub), 1)))
# 趟级
tl = {d: statistics.median([x["live_fps"] for x in rs]) for d, rs in trip.items()}
tum = {d: statistics.mean([x["units_mean"] for x in rs if x["units_mean"] is not None])
       for d, rs in trip.items() if any(x["units_mean"] is not None for x in rs)}
tu0 = {d: rs[0]["units0"] for d, rs in trip.items()}
ds = sorted(set(tum) & set(tl))
print("  趟级 ρ_P(units_mean, live) = %s (n=%d)" % (
    round(pearson([tum[d] for d in ds], [tl[d] for d in ds]), 4), len(ds)))
print("  趟级 ρ_P(units0,   live) = %s (n=%d)" % (
    round(pearson([tu0[d] for d in ds], [tl[d] for d in ds]), 4), len(ds)))

print("\n" + "=" * 112)
print("D. ρ(pre15, live) 样本池敏感性（§544 报 0.8925）")
print("=" * 112)
pools = {
    "严格 25s 窗（units0 非空）": strict,
    "全部可算 live>0 窗（含 4s settle 伪窗）": [r for r in rows if r["live_fps"] and r["live_fps"] > 0],
    "全部可算且 units0 非空": [r for r in rows if r["live_fps"] and r["live_fps"] > 0 and r["units0"] is not None],
    "严格窗 且 units0>0": [r for r in strict if r["units0"] > 0],
    "带内 units0 1180-1360 严格窗": [r for r in strict if 1180 <= r["units0"] <= 1360],
}
for name, pl in pools.items():
    pl = [r for r in pl if r["pre_fps15"] is not None]
    rp = pearson([r["pre_fps15"] for r in pl], [r["live_fps"] for r in pl])
    print("  %-38s n=%2d ρ_P=%s" % (name, len(pl), round(rp, 4) if rp is not None else "None"))
# 趟级
tpd = {d: rs[0]["pre_fps15"] for d, rs in trip.items() if rs[0]["pre_fps15"] is not None}
ds2 = sorted(set(tpd) & set(tl))
print("  %-38s n=%2d ρ_P=%s" % ("趟级（29 趟中位）", len(ds2),
                                round(pearson([tpd[d] for d in ds2], [tl[d] for d in ds2]), 4)))

print("\n" + "=" * 112)
print("E. 1180-1360 带内：快 vs 慢 的 (版本, sf, units0) 是否一一绑定")
print("=" * 112)
band = [r for r in strict if 1180 <= r["units0"] <= 1360]
for r in sorted(band, key=lambda x: (x["ts"], int(x["window"]))):
    fl = flags.get(r["dir"], {})
    print("  %-19s %-16s w%s units0=%-6d live=%6.2f pre15=%7.3f %-20s sf=%-7s map=%s units均=%s" % (
        r["ts"][:19], r["dir"][:16], r["window"], r["units0"], r["live_fps"], r["pre_fps15"],
        hlabel(r)[:20], str(fl.get("--h7-measure-start-frame", "default")),
        (r["map_sha256"] or "-")[:8], round(r["units_mean"], 1) if r["units_mean"] else "-"))
v_f = defaultdict(lambda: [0, 0])
for r in band:
    key = (hlabel(r), str(flags.get(r["dir"], {}).get("--h7-measure-start-frame", "default")))
    v_f[key][0 if r["live_fps"] >= 28 else 1] += 1
print("  (版本,sf) → [fast>=28, slow<28]:")
for k, v in sorted(v_f.items()):
    print("     %-24s sf=%-8s fast %d slow %d" % (k[0][:24], k[1], v[0], v[1]))

print("\n" + "=" * 112)
print("F. 版本内跨时段有没有真的快慢差（38244d2907e7f7fa：11-01 vs 11-03）")
print("=" * 112)
for h in ("38244d2907e7f7fa", "37a7c9cdf2ca97e3", "d019e8beecfb5fd8", "name:qc151_trip.harness3.py"):
    sub = [r for r in strict if hlabel(r) == h]
    bydir = defaultdict(list)
    for r in sub:
        bydir[r["dir"]].append(r)
    print("  %s:" % h[:28])
    for d, rs in sorted(bydir.items(), key=lambda x: x[1][0]["ts"]):
        ls = [x["live_fps"] for x in rs]
        print("     %-18s %-19s units0=%-6d live %6.2f..%6.2f 窗内 units 均 %.1f" % (
            d, rs[0]["ts"][:19], int(rs[0]["units0"]), min(ls), max(ls),
            statistics.mean([x["units_mean"] for x in rs if x["units_mean"] is not None])))
