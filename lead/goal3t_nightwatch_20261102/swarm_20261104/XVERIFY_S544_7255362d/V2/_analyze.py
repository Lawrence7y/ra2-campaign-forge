# -*- coding: utf-8 -*-
"""V2 时代效应核验：混淆表（harness/argv 旗标/map/gamemd/载体）+ 相关 + 趟内趟间方差。

自己实现 Pearson / Spearman（不调库）。窗口级与趟级都算（趟级防伪重复）。
"""
import csv
import json
import math
import os
import re
import statistics
from collections import defaultdict

OUT = os.path.dirname(os.path.abspath(__file__))


def ff(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ---------- 相关系数（自实现） ----------
def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def ranks(v):
    """平均秩（处理并列）。"""
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


# ---------- 读 census ----------
rows = []
with open(os.path.join(OUT, "census.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["base_tag"] != "mirror":
            continue
        r["live"] = ff(r["live_fps"])
        r["units0"] = ff(r["units0"])
        r["pre"] = ff(r["pre_fps15"])
        r["fps_avg"] = ff(r["fps_avg_json"])
        r["ts"] = r["fields_ts_first"] or ""
        rows.append(r)

# ---------- 趟级 argv 旗标 ----------
TRIPS = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
FLAGKEYS = ["--h7-measure-start-frame", "--h8-wait-trace", "--h8-wait-hz",
            "--h7-keep-rect-wait", "--fullscreen", "--measure"]
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


def hlabel(r):
    if r["harness_sha16"]:
        return r["harness_sha16"]
    ap = r["argv_harness"] or r["harness_path"]
    return "name:" + os.path.basename(ap) if ap else "UNKNOWN"


# ---------- 1. 关键对照带 units0 ∈ [1180,1360]：逐窗 + 全部混淆轴 ----------
print("=" * 118)
print("★ 1. units0 ∈ [1180,1360] 带内逐窗（自己重算的 live_fps）+ 混淆轴")
print("=" * 118)
band = sorted([r for r in rows if r["units0"] is not None and 1180 <= r["units0"] <= 1360],
              key=lambda x: x["ts"])
print("%-19s %-14s %2s %6s %8s %8s %18s %8s %6s %5s %12s %12s" % (
    "ts", "dir", "w", "units0", "live", "pre15", "harness", "startframe",
    "trace", "waitz", "map12", "gamemd12"))
for r in band:
    fl = flags.get(r["dir"], {})
    print("%-19s %-14s %2s %6s %8.2f %8.3f %18s %8s %6s %5s %12s %12s" % (
        r["ts"][:19], r["dir"][:14], r["window"], "%d" % r["units0"], r["live"],
        r["pre"] if r["pre"] is not None else float("nan"),
        hlabel(r)[:18], fl.get("--h7-measure-start-frame", "-"),
        "Y" if "--h8-wait-trace" in fl else "n",
        fl.get("--h8-wait-hz", "-"),
        (r["map_sha256"] or "-")[:12], (r["gamemd_sha256"] or "-")[:12]))

bydir = defaultdict(list)
for r in band:
    bydir[r["dir"]].append(r)
print("\n-- 带内趟级（live_fps 均值 / 极差）--")
for d, rs in sorted(bydir.items(), key=lambda x: x[1][0]["ts"]):
    ls = [x["live"] for x in rs]
    print("  %-14s %-19s n=%d units0=%d live %.2f..%.2f (mean %.2f) harness=%s sf=%s" % (
        d, rs[0]["ts"][:19], len(rs), int(rs[0]["units0"]), min(ls), max(ls),
        sum(ls) / len(ls), hlabel(rs[0])[:16],
        flags.get(d, {}).get("--h7-measure-start-frame", "-")))

print("\n带内 31+ 快窗所属 (harness, start-frame, 日期):")
fast = [r for r in band if r["live"] >= 28]
slow = [r for r in band if r["live"] < 20]
mid = [r for r in band if 20 <= r["live"] < 28]
for tag, grp in (("FAST>=28", fast), ("SLOW<20", slow), ("MID", mid)):
    s = set((hlabel(r), flags.get(r["dir"], {}).get("--h7-measure-start-frame", "-"),
             r["dir"], r["ts"][:10]) for r in grp)
    print("  %-8s n=%2d  %s" % (tag, len(grp), sorted(s)))
print("  快慢极值比：max(live)=%.2f min(live)=%.2f ratio=%.2fx" % (
    max(r["live"] for r in band), min(r["live"] for r in band),
    max(r["live"] for r in band) / min(r["live"] for r in band)))

# ---------- 2. 共线性判定 ----------
print("\n" + "=" * 118)
print("★ 2. 共线性判定：harness 版本 × 快/慢（全库窗，不止带内）")
print("=" * 118)
calc = [r for r in rows if r["live"] is not None and r["live"] > 0]
hv = defaultdict(list)
for r in calc:
    hv[hlabel(r)].append(r)
for h, rs in sorted(hv.items(), key=lambda x: min(y["ts"] for y in x[1])):
    ls = [x["live"] for x in rs]
    dates = sorted(set(x["ts"][:10] for x in rs))
    dirs = sorted(set(x["dir"] for x in rs))
    print("  %-30s n=%2d live %.2f..%.2f 中位 %6.2f 日期 %s" % (
        h, len(rs), min(ls), max(ls), statistics.median(ls), ",".join(dates)))
    print("        dirs: %s" % ", ".join(dirs))
    n_fast = sum(1 for l in ls if l >= 28)
    n_slow = sum(1 for l in ls if l < 20)
    print("        该版本内：快窗(>=28) %d, 慢窗(<20) %d  -> %s" % (
        n_fast, n_slow, "两态皆有（版本不能单独解释）" if n_fast and n_slow else "单态"))

print("\n-- 快/慢 × 日期 × harness 三轴共现（全库窗，按趟）--")
seen = set()
for r in sorted(calc, key=lambda x: x["ts"]):
    key = r["dir"]
    if key in seen:
        continue
    seen.add(key)
    ls = [x["live"] for x in calc if x["dir"] == key]
    st = "FAST" if statistics.median(ls) >= 28 else ("SLOW" if statistics.median(ls) < 20 else "MID")
    print("  %-19s %-14s %-6s harness=%-18s sf=%-5s map=%s" % (
        r["ts"][:19], key[:14], st, hlabel(r)[:18],
        flags.get(key, {}).get("--h7-measure-start-frame", "-"),
        (r["map_sha256"] or "-")[:12]))

# ---------- 3. 相关 ----------
print("\n" + "=" * 118)
print("★ 3. 相关系数（自实现 Pearson/Spearman）")
print("=" * 118)
pool = [r for r in rows if r["units0"] is not None and r["live"] is not None and r["live"] > 0]
print("窗口级样本 n=%d（units0 非空且 live 可算）" % len(pool))
xs = [r["live"] for r in pool]
ys = [r["pre"] for r in pool]
print("  ρ_Pearson(pre_fps15, live_fps) = %.4f" % pearson(ys, xs))
print("  ρ_Spearman(pre_fps15, live_fps) = %.4f" % spearman(ys, xs))
xu = [r["units0"] for r in pool]
print("  ρ_Pearson(units0, live_fps) = %.4f" % pearson(xu, xs))
print("  ρ_Spearman(units0, live_fps) = %.4f" % spearman(xu, xs))

# 趟级（防伪重复）
trip = defaultdict(list)
for r in pool:
    trip[r["dir"]].append(r)
tl = {d: statistics.median([x["live"] for x in rs]) for d, rs in trip.items()}
tu = {d: rs[0]["units0"] for d, rs in trip.items()}
tp = {d: rs[0]["pre"] for d, rs in trip.items() if rs[0]["pre"] is not None}
ds = [d for d in tl if d in tu and tu[d] is not None]
print("趟级样本 n=%d（同趟取 live 中位，units0/pre15 取趟值）" % len(ds))
print("  ρ_Pearson(units0, live) 趟级 = %.4f   ρ_Spearman = %.4f" % (
    pearson([tu[d] for d in ds], [tl[d] for d in ds]),
    spearman([tu[d] for d in ds], [tl[d] for d in ds])))
ds2 = [d for d in ds if d in tp]
print("  ρ_Pearson(pre15, live) 趟级 = %.4f   ρ_Spearman = %.4f   (n=%d)" % (
    pearson([tp[d] for d in ds2], [tl[d] for d in ds2]),
    spearman([tp[d] for d in ds2], [tl[d] for d in ds2]), len(ds2)))

print("\n-- 固定 harness 版本内 ρ(units0, live_fps) --")
for h, rs in sorted(hv.items()):
    sub = [x for x in rs if x["units0"] is not None and x["units0"] > 0]
    if len(sub) >= 3:
        print("  %-30s n=%2d  ρ_P=%.4f  ρ_S=%.4f  units0 %.0f..%.0f live %.2f..%.2f" % (
            h, len(sub), pearson([x["units0"] for x in sub], [x["live"] for x in sub]),
            spearman([x["units0"] for x in sub], [x["live"] for x in sub]),
            min(x["units0"] for x in sub), max(x["units0"] for x in sub),
            min(x["live"] for x in sub), max(x["live"] for x in sub)))
    else:
        print("  %-30s n=%2d  样本不足（<3）" % (h, len(sub)))

# harness 版本作为序数 + 日期作为混淆
print("\n-- 版本 vs 日期 vs 速度：每个版本的趟级中位 live --")
for h, rs in sorted(hv.items(), key=lambda x: min(y["ts"] for y in x[1])):
    tmed = {}
    for d, sub in trip.items():
        if hlabel(sub[0]) == h:
            tmed[d] = statistics.median([x["live"] for x in sub])
    if tmed:
        print("  %-30s 趟级: %s" % (h, {k: round(v, 2) for k, v in sorted(tmed.items())}))

# ---------- 4. 同 units0 档内跨时段（>=3 次） ----------
print("\n" + "=" * 118)
print("★ 4. 同 units0 档（精确值，n>=3）跨时段极差 + 版本/旗标是否同变")
print("=" * 118)
gu = defaultdict(list)
for r in calc:
    if r["units0"] is not None:
        gu[int(r["units0"])].append(r)
for u in sorted(gu):
    rs = gu[u]
    if len(rs) < 3:
        continue
    ls = [x["live"] for x in rs]
    hs = set(hlabel(x) for x in rs)
    sfs = set(flags.get(x["dir"], {}).get("--h7-measure-start-frame", "-") for x in rs)
    maps = set((x["map_sha256"] or "-")[:12] for x in rs)
    print("  units0=%-5d n=%2d live %.2f..%.2f (%.2fx) harness数=%d 版本 %s sf %s map %s 日期 %s" % (
        u, len(rs), min(ls), max(ls), max(ls) / min(ls), len(hs),
        sorted(h[:8] for h in hs), sorted(sfs), sorted(maps),
        sorted(set(x["ts"][:10] for x in rs))))
    if len(hs) > 1 or len(sfs) > 1 or len(maps) > 1:
        print("      ⇒ 该档内版本/旗标/地图并非全同，跨时段差与工具链差**部分可分**")
    else:
        print("      ⇒ 该档内版本+旗标+地图全同（工具链恒定），差值只能来自时段/机器")

# ---------- 5. 趟内 vs 趟间方差 ----------
print("\n" + "=" * 118)
print("★ 5. 趟内窗间极差 vs 趟间极差")
print("=" * 118)
within = []
for d, rs in trip.items():
    ls = [x["live"] for x in rs]
    if len(ls) >= 2:
        within.append((d, len(ls), min(ls), max(ls), max(ls) - min(ls),
                       max(ls) / min(ls) if min(ls) > 0 else float("inf")))
print("同一 trip_id 内多窗（n=%d 趟）窗间极差：" % len(within))
for d, n, a, b, rng, ratio in sorted(within, key=lambda x: -x[5]):
    print("   %-16s n=%d live %6.2f..%6.2f  极差 %6.2f  倍率 %5.2fx" % (d, n, a, b, rng, ratio))
print("   窗间极差中位 = %.2f fps ; 窗间倍率中位 = %.2fx" % (
    statistics.median([w[4] for w in within]), statistics.median([w[5] for w in within])))
btm = [statistics.median([x["live"] for x in rs]) for rs in trip.values()]
print("趟级中位 live 的趟间极差 = %.2f (%.2f..%.2f, %.2fx)" % (
    max(btm) - min(btm), min(btm), max(btm), max(btm) / min(btm)))
# 同 units0 带内：趟间
btm_band = [statistics.median([x["live"] for x in rs]) for d, rs in trip.items()
            if rs[0]["units0"] is not None and 1180 <= rs[0]["units0"] <= 1360]
print("带内（units0 1180-1360）趟间中位 live 极差 = %.2f (%.2f..%.2f, %.2fx)" % (
    max(btm_band) - min(btm_band), min(btm_band), max(btm_band),
    max(btm_band) / min(btm_band)))
within_band = [w for w in within if trip[w[0]][0]["units0"] is not None
               and 1180 <= trip[w[0]][0]["units0"] <= 1360]
print("带内趟内窗间极差中位 = %.2f ; 倍率中位 = %.2fx" % (
    statistics.median([w[4] for w in within_band]),
    statistics.median([w[5] for w in within_band])))
