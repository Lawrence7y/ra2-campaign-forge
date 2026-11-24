# -*- coding: utf-8 -*-
"""V2 混淆排查补充：
 A. 点名窗的 live_fps 手算复核（打印原始首末沿）
 B. 带内 fast/slow × harness 版本 列联表 + Fisher 精确检验（自实现）
 C. 帧成本构成（units/infantry/aircraft/techno/items/ws_kb）跨趟对比
 D. 宿主争用指纹：采样缺口 gap_s / hz_effective 与 live_fps 的关系
 E. gamemd / map / 载体件数 / t_clock 唯一性
"""
import csv
import glob
import json
import math
import os
import statistics
from collections import defaultdict

ROOT = r"D:\Project\ra2-campaign-forge"
TRIPS = ROOT + r"\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUT = os.path.dirname(os.path.abspath(__file__))

# ---------- A. 手算复核 ----------
NAMED = [
    ("l3_1101v4d", 0, "11-01 16:48 快"),
    ("l3_1101v4e", 0, "11-03 11:20 快"),
    ("l1c_20261021", 0, "10-21 19:03 慢（§544 说 units≈881）"),
    ("l3_20261031hb", 0, "10-31 20:15 慢"),
    ("l3_20261021", 0, "10-21 21:10 慢（带内）"),
    ("l3_1101v3a", 0, "11-01 07:04 慢"),
]
print("=" * 110)
print("A. 逐窗口手算：live_fps=(f_last-f_first)/(t_last-t_first)，直接读 frame_edges")
print("=" * 110)
for d, w, label in NAMED:
    p = os.path.join(TRIPS, d, "measure_w%d.json" % w)
    j = json.load(open(p, encoding="utf-8"))
    e = j["frame_edges"]
    f0, t0 = e[0]
    f1, t1 = e[-1]
    live = (f1 - f0) / (t1 - t0)
    print("  %-16s w%d %-28s edges[0]=(%d, %.6f) edges[-1]=(%d, %.6f)" % (d, w, label, f0, t0, f1, t1))
    print("      df=%d  dt=%.6f s  => live=%.4f fps   | json fps_avg=%.4f p50=%.4f units0=%s pre15=%s n_edges=%s" % (
        f1 - f0, t1 - t0, live, j["stats"]["fps_avg"], j["stats"].get("fps_p50") or float("nan"),
        j["gate"].get("units0"), j["gate"].get("pre_fps15"), j["stats"].get("n_edges")))
    print("      map=%s gamemd=%s span=%.3f settle=%.1f hz=%s t_clock=%s schema=%s trip=%s" % (
        (j.get("map_sha256") or "")[:16], (j.get("gamemd_sha256") or "")[:16],
        j.get("span_s") or 0, j.get("settle_s") or 0, j.get("hz"), j.get("t_clock"),
        j.get("schema"), j.get("trip_id")))
    print("      stats keys: %s" % sorted(j["stats"].keys()))

# ---------- 载入 census ----------
rows = []
with open(os.path.join(OUT, "census.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["base_tag"] != "mirror":
            continue
        for k in ("live_fps", "units0", "pre_fps15", "fps_avg_json", "gap_s", "span_s", "max_stall_json"):
            try:
                r[k] = float(r[k])
            except (TypeError, ValueError):
                r[k] = None
        rows.append(r)


def hlabel(r):
    if r["harness_sha16"]:
        return r["harness_sha16"]
    ap = r["argv_harness"] or r["harness_path"]
    return "name:" + os.path.basename(ap) if ap else "UNKNOWN"


# ---------- B. 列联表 + Fisher ----------
print("\n" + "=" * 110)
print("B. 带内 units0∈[1180,1360]：fast(>=28) / slow(<20) × harness 版本")
print("=" * 110)
band = [r for r in rows if r["units0"] is not None and 1180 <= r["units0"] <= 1360
        and r["live_fps"] is not None]
tab = defaultdict(lambda: [0, 0])
for r in band:
    tab[hlabel(r)][0 if r["live_fps"] >= 28 else 1] += 1
for h, (nf, ns) in sorted(tab.items()):
    print("   %-32s fast %2d  slow %2d" % (h, nf, ns))
print("   带内 units0 分布：fast %s  slow %s" % (
    sorted(set(int(r["units0"]) for r in band if r["live_fps"] >= 28)),
    sorted(set(int(r["units0"]) for r in band if r["live_fps"] < 20))))
print("   带内 measure-start-frame：fast %s slow %s" % (
    sorted(set((r["dir"]) for r in band if r["live_fps"] >= 28)),
    sorted(set(r["dir"] for r in band if r["live_fps"] < 20))))


def fisher_p(a, b, c, dd):
    """双侧 Fisher 精确检验（超几何）。2x2: [[a,b],[c,d]]"""
    n = a + b + c + dd
    r1 = a + b
    c1 = a + c

    def C(n, k):
        if k < 0 or k > n:
            return 0
        return math.comb(n, k)

    denom = C(n, c1)
    p_obs = C(r1, a) * C(n - r1, c1 - a) / denom
    p = 0.0
    lo = max(0, c1 - (n - r1))
    hi = min(r1, c1)
    for x in range(lo, hi + 1):
        px = C(r1, x) * C(n - r1, c1 - x) / denom
        if px <= p_obs + 1e-12:
            p += px
    return p


# 全库（不含 units0=0 伪档）高负载带内：v4 vs 非 v4
V4 = "38244d2907e7f7fa"
a = sum(1 for r in band if hlabel(r) == V4 and r["live_fps"] >= 28)
b = sum(1 for r in band if hlabel(r) == V4 and r["live_fps"] < 28)
c = sum(1 for r in band if hlabel(r) != V4 and r["live_fps"] >= 28)
d2 = sum(1 for r in band if hlabel(r) != V4 and r["live_fps"] < 28)
print("\n   2x2 [v4: fast %d slow %d | 非v4: fast %d slow %d] 双侧 Fisher p = %.6g" % (
    a, b, c, d2, fisher_p(a, b, c, d2)))

# 同一对：protocol（measure-start-frame 400 vs 800）
SF400 = {"l3_20261031ha", "l3_20261031hb", "l3_1101v3a", "l3_1101v3b"}
SF800 = {"l3_1101v4c", "l3_1101v4d", "l3_1101v4e"}
a = sum(1 for r in band if r["dir"] in SF800 and r["live_fps"] >= 28)
b = sum(1 for r in band if r["dir"] in SF800 and r["live_fps"] < 28)
c = sum(1 for r in band if r["dir"] in SF400 and r["live_fps"] >= 28)
d2 = sum(1 for r in band if r["dir"] in SF400 and r["live_fps"] < 28)
print("   2x2 [sf=800: fast %d slow %d | sf=400: fast %d slow %d] Fisher p = %.6g" % (
    a, b, c, d2, fisher_p(a, b, c, d2)))
u800 = [int(r["units0"]) for r in band if r["dir"] in SF800]
u400 = [int(r["units0"]) for r in band if r["dir"] in SF400]
print("   ⇒ sf=800 组 units0 %s (min %d) ; sf=400 组 units0 %s (min %d) —— 协议换了，负载也一起换了" % (
    sorted(set(u800)), min(u800), sorted(set(u400)), min(u400)))

# ---------- C. 帧成本构成 ----------
print("\n" + "=" * 110)
print("C. 带内各趟 counters 首帧构成（units/inf/air/techno/items/ws_kb）")
print("=" * 110)
dirs = sorted(set(r["dir"] for r in band), key=lambda d: min(r["ts"] if "ts" in r else "" for r in band if r["dir"] == d) or d)
order = []
seen = set()
for r in sorted(band, key=lambda x: x["fields_ts_first"]):
    if r["dir"] not in seen:
        seen.add(r["dir"])
        order.append(r["dir"])
print("  %-16s %-19s %-20s %6s %6s %5s %5s %7s %9s" % (
    "dir", "ts", "harness", "units", "inf", "air", "tech", "g_items", "ws_kb"))
for d in order:
    p = os.path.join(TRIPS, d, "measure_w0.json")
    j = json.load(open(p, encoding="utf-8"))
    cs = j.get("counters") or [{}]
    g = j["gate"]
    row = None
    for x in cs:
        if x.get("units") is not None:
            row = x
            break
    row = row or {}
    ts = [r for r in band if r["dir"] == d][0]
    print("  %-16s %-19s %-20s %6s %6s %5s %5s %7s %9s  units0=%s pre15=%s" % (
        d, ts["fields_ts_first"][:19], hlabel(ts),
        row.get("units"), row.get("infantry"), row.get("aircraft"), row.get("techno"),
        row.get("g_items"), row.get("ws_kb"), g.get("units0"), g.get("pre_fps15")))

# 末帧构成（窗尾）
print("\n  窗尾（同份 json 最后一条 counter 读数）：")
for d in order:
    p = os.path.join(TRIPS, d, "measure_w0.json")
    j = json.load(open(p, encoding="utf-8"))
    cs = j.get("counters") or [{}]
    last = cs[-1]
    print("  %-16s units=%-5s inf=%-5s air=%-4s techno=%-5s g=%-5s b=%-5s ws=%-8s" % (
        d, last.get("units"), last.get("infantry"), last.get("aircraft"),
        last.get("techno"), last.get("g"), last.get("b"), last.get("ws_kb")))

# ---------- D. 宿主争用指纹 ----------
print("\n" + "=" * 110)
print("D. 采样缺口（samples.t dt>10ms 累计，秒）vs live_fps —— 宿主争用指纹")
print("=" * 110)
calc = [r for r in rows if r["live_fps"] is not None and r["live_fps"] > 0]
print("  %-19s %-16s %-20s %8s %8s %7s %7s" % ("ts", "dir", "harness", "live", "gap_s", "gap_n", "max_stall"))
for r in sorted(calc, key=lambda x: x["fields_ts_first"]):
    print("  %-19s %-16s %-20s %8.2f %8.3f %7s %7s" % (
        r["fields_ts_first"][:19], r["dir"][:16], hlabel(r)[:20],
        r["live_fps"], r["gap_s"] or 0.0, r["gap_n"], (r["max_stall_json"] or 0)))
xs = [r["live_fps"] for r in calc]
ys = [r["gap_s"] or 0.0 for r in calc]


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    dx = math.sqrt(sum((a - mx) ** 2 for a in xs))
    dy = math.sqrt(sum((b - my) ** 2 for b in ys))
    return num / (dx * dy) if dx > 0 and dy > 0 else None


print("  ρ_Pearson(live_fps, 采样缺口 gap_s) = %s (n=%d)" % (pearson(xs, ys), len(xs)))
print("  快窗(>=28) gap_s 中位 = %.3f ；慢窗(<20) gap_s 中位 = %.3f" % (
    statistics.median([r["gap_s"] or 0 for r in calc if r["live_fps"] >= 28]),
    statistics.median([r["gap_s"] or 0 for r in calc if r["live_fps"] < 20])))

# ---------- E. 混淆轴唯一性 ----------
print("\n" + "=" * 110)
print("E. 混淆轴唯一性（全库可算窗）")
print("=" * 110)
for field in ("map_sha256", "gamemd_sha256", "t_clock", "schema", "hz", "span_s", "settle_s"):
    vals = defaultdict(set)
    for r in calc:
        vals[str(r[field])[:16]].add(r["dir"])
    print("  %-12s 取值 %d 个：%s" % (field, len(vals), {k: len(v) for k, v in sorted(vals.items())}))
band_dirs = sorted(set(r["dir"] for r in band))
print("  带内各趟 map/gamemd：")
for d in band_dirs:
    r = [x for x in band if x["dir"] == d][0]
    print("    %-16s map=%s gamemd=%s hz=%s span=%s settle=%s" % (
        d, (r["map_sha256"] or "-")[:16], (r["gamemd_sha256"] or "-")[:16],
        r["hz"], r["span_s"], r["settle_s"]))

# 载体件数
print("\n  载体（carrier）件数：")
for d in band_dirs:
    rec = os.path.join(TRIPS, d, "carrier_creation_receipt.json")
    n = None
    if os.path.exists(rec):
        j = json.load(open(rec, encoding="utf-8"))
        if isinstance(j, list):
            n = len(j)
        elif isinstance(j, dict):
            for k, v in j.items():
                if isinstance(v, list):
                    n = "%s=%d" % (k, len(v))
                    break
    print("    %-16s carrier=%s" % (d, n))
