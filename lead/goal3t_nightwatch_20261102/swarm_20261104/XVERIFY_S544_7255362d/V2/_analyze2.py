# -*- coding: utf-8 -*-
"""V2 严格口径复核：只取真 25 秒测量窗（verdict==ok ∧ span_s==25.0）。

排除 no_advance 的 4 秒 settle 伪窗（那些不是测量窗）。重算：
 - 快慢 × harness 版本 × 协议(--h7-measure-start-frame) × 地图 列联
 - 同 units0 精确档跨时段：有没有「同负载既快又慢」的实例
 - ρ(pre15, live) / ρ(units0, live)：窗级 + 趟级，全局 + 固定版本内
 - 趟内 vs 趟间极差（中位数）
 - hz_effective（轮询有效性）作为宿主争用指纹
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


def hlabel(r):
    if r["harness_sha16"]:
        return r["harness_sha16"]
    ap = r["argv_harness"] or r["harness_path"]
    return "name:" + os.path.basename(ap) if ap else "UNKNOWN"


extra = {}
for d in os.listdir(TRIPS):
    p = os.path.join(TRIPS, d, "measure_w0.json")
    if os.path.exists(p):
        j = json.load(open(p, encoding="utf-8"))
        st = j.get("stats") or {}
        cc = j.get("carrier") or {}
        extra[d] = {"hz_effective": st.get("hz_effective"),
                    "n_multi_advance": st.get("n_multi_advance"),
                    "tick_miss": st.get("tick_miss")}

rows = []
with open(os.path.join(OUT, "census.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["base_tag"] != "mirror":
            continue
        for k in ("live_fps", "units0", "pre_fps15", "fps_avg_json", "fps_p50_json", "gap_s", "span_s"):
            r[k] = ff(r[k])
        r["ts"] = r["fields_ts_first"] or ""
        rows.append(r)

strict = [r for r in rows if r["verdict"] == "ok" and r["span_s"] == 25.0
          and r["live_fps"] is not None and r["live_fps"] > 0]
settle_fake = [r for r in rows if r["live_fps"] is not None and r["live_fps"] > 0
               and not (r["verdict"] == "ok" and r["span_s"] == 25.0)]

print("=" * 112)
print("0. 口径清洗：可算 live_fps 的窗共 %d 个，其中真 25s 测量窗 %d 个，" % (
    len(strict) + len(settle_fake), len(strict)))
print("   另有 %d 个是 verdict=no_advance / span=4.0 的 settle 伪窗（不能当测量窗用）：" % len(settle_fake))
for r in sorted(settle_fake, key=lambda x: x["ts"]):
    print("     %-19s %-16s w%s span=%-5s verdict=%-11s units0=%-6s live=%7.2f (其实是 settle 1.5-4s 段)" % (
        r["ts"][:19], r["dir"][:16], r["window"], r["span_s"], r["verdict"],
        r["units0"], r["live_fps"]))

print("\n" + "=" * 112)
print("1. 严格窗池（n=%d，%d 趟）逐趟：日期 × 版本 × 协议 × 地图 × 负载 × live" % (
    len(strict), len(set(r["dir"] for r in strict))))
print("%-19s %-16s %-20s %-8s %-14s %6s %6s %7s %7s" % (
    "ts", "dir", "harness", "sf帧", "map", "units0", "n_win", "live中位", "live极差"))
trip = defaultdict(list)
for r in strict:
    trip[r["dir"]].append(r)
for d, rs in sorted(trip.items(), key=lambda x: x[1][0]["ts"]):
    ls = [x["live_fps"] for x in rs]
    fl = flags.get(d, {})
    print("%-19s %-16s %-20s %-8s %-14s %6s %6d %7.2f %7.2f  gap_s=%.2f hz_eff=%s" % (
        rs[0]["ts"][:19], d[:16], hlabel(rs[0])[:20],
        str(fl.get("--h7-measure-start-frame", "default")),
        (rs[0]["map_sha256"] or "-")[:14], int(rs[0]["units0"]) if rs[0]["units0"] is not None else "-",
        len(rs), statistics.median(ls), max(ls) - min(ls),
        sum(x["gap_s"] or 0 for x in rs), extra.get(d, {}).get("hz_effective")))

# ---- 版本 × 快慢（严格窗）----
print("\n" + "=" * 112)
print("2. 严格窗池：harness 版本内有没有既快又慢")
hv = defaultdict(list)
for r in strict:
    hv[hlabel(r)].append(r)
for h, rs in sorted(hv.items(), key=lambda x: min(y["ts"] for y in x[1])):
    ls = [x["live_fps"] for x in rs]
    dates = sorted(set(x["ts"][:10] for x in rs))
    units = sorted(set(int(x["units0"]) for x in rs if x["units0"] is not None))
    maps = sorted(set((x["map_sha256"] or "-")[:12] for x in rs))
    print("  %-30s n=%2d live %6.2f..%6.2f 日期 %s units0 %s map %s" % (
        h, len(rs), min(ls), max(ls), ",".join(dates), units, maps))

# ---- 同 units0 精确档跨日期：有没有同负载既快又慢 ----
print("\n" + "=" * 112)
print("3. 严格窗池：同 units0（精确）跨日期/跨版本 —— 判定「同负载跨时段」是否成立")
gu = defaultdict(list)
for r in strict:
    if r["units0"] is not None:
        gu[int(r["units0"])].append(r)
any_cross_era_same_load = 0
for u in sorted(gu):
    rs = gu[u]
    if len(rs) < 3:
        continue
    dates = sorted(set(x["ts"][:10] for x in rs))
    vers = sorted(set(hlabel(x) for x in rs))
    ls = [x["live_fps"] for x in rs]
    fast_and_slow = (max(ls) >= 28 and min(ls) < 20)
    print("  units0=%-5d n=%2d dates %s vers %d live %6.2f..%6.2f %s" % (
        u, len(rs), ",".join(dates), len(vers), min(ls), max(ls),
        "★既快又慢" if fast_and_slow else ""))
    if len(dates) > 1 and fast_and_slow:
        any_cross_era_same_load += 1
print("  ⇒ 同 units0 且跨日期且既快又慢的档数 = %d" % any_cross_era_same_load)

# 放宽：units0 带内（±50）跨日期快慢对照
print("\n  放宽到 ±50 units0 的同负载跨时段对照（各趟中位 live）：")
tinfo = []
for d, rs in trip.items():
    if rs[0]["units0"] is None:
        continue
    tinfo.append((rs[0]["units0"], statistics.median([x["live_fps"] for x in rs]),
                  d, rs[0]["ts"][:10], hlabel(rs[0]),
                  (rs[0]["map_sha256"] or "-")[:12],
                  str(flags.get(d, {}).get("--h7-measure-start-frame", "default"))))
tinfo.sort()
for a in range(len(tinfo)):
    for b in range(a + 1, len(tinfo)):
        u1, l1, d1, dt1, h1, m1, sf1 = tinfo[a]
        u2, l2, d2, dt2, h2, m2, sf2 = tinfo[b]
        if abs(u1 - u2) <= 50 and dt1 != dt2 and (l1 >= 28) != (l2 >= 28):
            print("     units0 %.0f(%.2f,%s,%s,sf=%s) vs %.0f(%.2f,%s,%s,sf=%s) 差 %.2fx | 版本同=%s 地图同=%s" % (
                u1, l1, dt1, h1[:8], sf1, u2, l2, dt2, h2[:8], sf2,
                max(l1, l2) / min(l1, l2), h1 == h2, m1 == m2))

# ---- 4. 相关 ----
print("\n" + "=" * 112)
print("4. 相关（严格窗池）")
pool = [r for r in strict if r["units0"] is not None]
print("  窗级 n=%d" % len(pool))
print("    ρ_P(pre15,live)=%s  ρ_S=%s" % (
    round(pearson([r["pre_fps15"] for r in pool], [r["live_fps"] for r in pool]), 4),
    round(spearman([r["pre_fps15"] for r in pool], [r["live_fps"] for r in pool]), 4)))
print("    ρ_P(units0,live)=%s ρ_S=%s" % (
    round(pearson([r["units0"] for r in pool], [r["live_fps"] for r in pool]), 4),
    round(spearman([r["units0"] for r in pool], [r["live_fps"] for r in pool]), 4)))
tl = {d: statistics.median([x["live_fps"] for x in rs]) for d, rs in trip.items()}
tu = {d: rs[0]["units0"] for d, rs in trip.items() if rs[0]["units0"] is not None}
tp = {d: rs[0]["pre_fps15"] for d, rs in trip.items() if rs[0]["pre_fps15"] is not None}
ds = [d for d in tl if d in tu]
print("  趟级 n=%d" % len(ds))
print("    ρ_P(units0,live)=%s ρ_S=%s" % (
    round(pearson([tu[d] for d in ds], [tl[d] for d in ds]), 4),
    round(spearman([tu[d] for d in ds], [tl[d] for d in ds]), 4)))
ds2 = [d for d in ds if d in tp]
print("    ρ_P(pre15,live)=%s ρ_S=%s (n=%d)" % (
    round(pearson([tp[d] for d in ds2], [tl[d] for d in ds2]), 4),
    round(spearman([tp[d] for d in ds2], [tl[d] for d in ds2]), 4), len(ds2)))

print("\n  固定版本内 ρ(units0, live)：")
for h, rs in sorted(hv.items()):
    sub = [x for x in rs if x["units0"] is not None]
    us = sorted(set(int(x["units0"]) for x in sub))
    tag = "" if len(sub) >= 4 else "  [n 过小]"
    rp = pearson([x["units0"] for x in sub], [x["live_fps"] for x in sub]) if len(sub) >= 3 else None
    rs_ = spearman([x["units0"] for x in sub], [x["live_fps"] for x in sub]) if len(sub) >= 3 else None
    print("    %-30s n=%2d units0 档 %s ρ_P=%s ρ_S=%s%s" % (
        h, len(sub), us, round(rp, 4) if rp is not None else "None(零方差/n<3)",
        round(rs_, 4) if rs_ is not None else "None", tag))

print("\n  固定地图内 ρ(units0, live)：")
hm = defaultdict(list)
for r in pool:
    hm[(r["map_sha256"] or "-")[:16]].append(r)
for m, rs in sorted(hm.items(), key=lambda x: -len(x[1])):
    us = sorted(set(int(x["units0"]) for x in rs))
    hs = sorted(set(hlabel(x) for x in rs))
    rp = pearson([x["units0"] for x in rs], [x["live_fps"] for x in rs]) if len(rs) >= 3 else None
    rsp = spearman([x["units0"] for x in rs], [x["live_fps"] for x in rs]) if len(rs) >= 3 else None
    print("    map=%-17s n=%2d units0 %s 版本数 %d ρ_P=%s ρ_S=%s" % (
        m, len(rs), us, len(hs),
        round(rp, 4) if rp is not None else "None",
        round(rsp, 4) if rsp is not None else "None"))

# 固定版本+固定协议（v4 & sf=800）内，pre15 与 live
print("\n  固定版本 38244d2907e7f7fa 内 ρ(pre15,live)（该版本 units0 全在 1189-1229）：")
sub = hv.get("38244d2907e7f7fa", [])
print("    n=%d ρ_P=%s ρ_S=%s units0 %s" % (
    len(sub), round(pearson([x["pre_fps15"] for x in sub], [x["live_fps"] for x in sub]), 4),
    round(spearman([x["pre_fps15"] for x in sub], [x["live_fps"] for x in sub]), 4),
    sorted(set(int(x["units0"]) for x in sub))))

# ---- 5. 趟内 vs 趟间 ----
print("\n" + "=" * 112)
print("5. 趟内窗间极差 vs 趟间极差（严格窗池）")
w = []
for d, rs in trip.items():
    ls = [x["live_fps"] for x in rs]
    if len(ls) >= 2:
        w.append((d, len(ls), min(ls), max(ls), max(ls) - min(ls)))
for x in sorted(w, key=lambda y: -y[4]):
    print("   %-18s n=%d %6.2f..%6.2f 极差 %6.2f" % (x[0], x[1], x[2], x[3], x[4]))
print("   趟内窗间极差中位 = %.2f fps (n_趟=%d)" % (statistics.median([x[4] for x in w]), len(w)))
btm = sorted(tl.values())
print("   趟级中位 live：min %.2f max %.2f 极差 %.2f (%.2fx)" % (
    min(btm), max(btm), max(btm) - min(btm), max(btm) / min(btm)))
vals = list(tl.values())
print("   趟间总变差 SD=%.2f；趟内 SD 中位=%.3f" % (
    statistics.pstdev(vals),
    statistics.median([statistics.pstdev([x["live_fps"] for x in rs])
                       for d, rs in trip.items() if len(rs) >= 2])))
# 带内
band_d = [d for d, rs in trip.items() if rs[0]["units0"] is not None and 1180 <= rs[0]["units0"] <= 1360]
bl = [tl[d] for d in band_d]
print("   带内(units0 1180-1360) 趟级中位 live：n=%d 极差 %.2f (%.2fx) 值 %s" % (
    len(bl), max(bl) - min(bl), max(bl) / min(bl), {d: round(tl[d], 2) for d in sorted(band_d)}))
wb = [x for x in w if x[0] in band_d]
print("   带内趟内窗间极差中位 = %.2f (n=%d)" % (statistics.median([x[4] for x in wb]), len(wb)))

# ---- 6. 同趟内 live 与窗序 / 窗内 units 衰减 ----
print("\n" + "=" * 112)
print("6. 带内各趟：窗序 vs live vs 窗尾 units（ battle 相位是否在窗内衰减负载）")
for d in sorted(band_d, key=lambda x: trip[x][0]["ts"]):
    parts = []
    for r in sorted(trip[d], key=lambda x: int(x["window"])):
        p = os.path.join(TRIPS, d, "measure_w%s.json" % r["window"])
        j = json.load(open(p, encoding="utf-8"))
        cs = j.get("counters") or [{}]
        u_end = cs[-1].get("units")
        parts.append("w%s live=%.2f units末=%s" % (r["window"], r["live_fps"], u_end))
    print("   %-18s %s" % (d, "  |  ".join(parts)))
