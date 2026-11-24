# -*- coding: utf8 -*-
"""RC-G：自建的判决性检验。
(a) 带容差的「同负载跨日期」对照（报告只用 units0 精确相等，太脆）
(b) 那 6 对 >3x 跨版本窗对，是否同一战斗相位（绝对帧号）——相位混淆检验
(c) 混淆轴：tz / 载体件数 / map / gamemd
(d) 「3 倍」这个数字在带内容量差下能否复现
"""
import csv, json, os, statistics
from collections import defaultdict

ROOT = r"D:\Project\ra2-campaign-forge"
MIRROR = ROOT + r"\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUT = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(OUT, "rc_census.csv"), encoding="utf-8")))
for r in rows:
    for k in ("units0", "live", "span_s", "c_units", "f0", "f1", "pre_fps15", "gap_s"):
        try:
            r[k] = float(r[k])
        except (TypeError, ValueError):
            r[k] = None
M = [r for r in rows if r["base_tag"] == "mirror"]
P3 = [r for r in M if r["verdict"] == "ok" and r["span_s"] == 25.0 and r["live"] and r["live"] > 0
      and r["units0"] is not None]
L3 = [r for r in P3 if (r["map_sha256"] or "").startswith("f3bb0a4e")]

print("== (a) 趟级 · 同图 · units0 容差 ±20 的跨日期对照 ==")
tr = {}
for r in L3:
    tr.setdefault(r["dir"], []).append(r)
T = [dict(dir=d, live=statistics.median(x["live"] for x in rs), units0=rs[0]["units0"],
          date=(rs[0]["ts"] or "")[:10], sha=rs[0]["sha16"] or "harness3",
          f0=min(x["f0"] for x in rs if x["f0"])) for d, rs in tr.items()]
for t in sorted(T, key=lambda x: x["units0"]):
    print("   units0=%-6d live=%6.2f %-12s %-16s %s f0=%d" % (
        t["units0"], t["live"], t["date"], t["dir"], t["sha"][:10], t["f0"]))
seen = []
for a, b in [(a, b) for i, a in enumerate(T) for b in T[i+1:]]:
    if abs(a["units0"] - b["units0"]) <= 20 and a["date"] != b["date"]:
        seen.append((max(a["live"], b["live"])/min(a["live"], b["live"]), a, b))
print("  ±20 跨日期趟对 n=%d" % len(seen))
for ratio, a, b in sorted(seen, reverse=True):
    print("   %5.2fx  %s %s(u0=%d,live=%.2f) vs %s %s(u0=%d,live=%.2f) 同版本?%s" % (
        ratio, a["date"], a["dir"], a["units0"], a["live"], b["date"], b["dir"], b["units0"], b["live"],
        a["sha"] == b["sha"]))
print("  ⇒ 同图·±20·跨日期 最大倍率 %.2fx ；>3x 的对数 %d/%d" % (
    max(r for r, _, _ in seen) if seen else 0, sum(1 for r, _, _ in seen if r > 3), len(seen)))

print("\n== (b) 报告称「所有 >3x 都跨版本」的那 6 对窗对：相位（绝对帧号）是否同一 ==")
import itertools
pairs = []
for a, b in itertools.combinations(L3, 2):
    if a["dir"] == b["dir"] or not a["c_units"] or not b["c_units"]:
        continue
    if abs(a["c_units"] - b["c_units"]) > 40:
        continue
    ratio = max(a["live"], b["live"])/min(a["live"], b["live"])
    if (a["sha16"] or "h3") != (b["sha16"] or "h3") and ratio > 3:
        pairs.append((ratio, a, b))
for ratio, a, b in sorted(pairs, reverse=True):
    print("  %.2fx  %s w%s f=%d..%d live=%6.2f (%s) || %s w%s f=%d..%d live=%6.2f (%s)  帧距=%d" % (
        ratio, a["dir"], a["window"], a["f0"], a["f1"], a["live"], (a["sha16"] or "h3")[:8],
        b["dir"], b["window"], b["f0"], b["f1"], b["live"], (b["sha16"] or "h3")[:8],
        abs((a["f0"]+a["f1"])/2 - (b["f0"]+b["f1"])/2)))
print("  ⇒ 相位差中位 %.0f 帧；最小 %d 帧" % (
    statistics.median([abs((a["f0"]+a["f1"])/2-(b["f0"]+b["f1"])/2) for _, a, b in pairs]),
    min(int(abs((a["f0"]+a["f1"])/2-(b["f0"]+b["f1"])/2)) for _, a, b in pairs)))

print("\n== (c) 混淆轴 ==")
for r in L3:
    pass
maps = defaultdict(set)
for r in P3:
    maps[(r["map_sha256"] or "")[:12]].add(r["dir"])
print("  map_sha256 取值数=%d（严格窗）" % len(maps))
print("  gamemd 唯一值：%s" % set((r["gamemd"] or "")[:16] for r in P3))
nc = {}
for d in set(r["dir"] for r in L3):
    p = os.path.join(MIRROR, d, "carrier_creation_receipt.json")
    nc[d] = json.load(open(p, encoding="utf-8")).get("files_copied") if os.path.exists(p) else "无文件"
print("  载体 files_copied（L3 各趟）：%s" % sorted(set(map(str, nc.values()))))
tzs = set()
for d in set(r["dir"] for r in P3):
    p = os.path.join(MIRROR, d, "qc151_fields.json")
    if os.path.exists(p):
        for x in json.load(open(p, encoding="utf-8")):
            if isinstance(x, dict) and isinstance(x.get("ts"), str):
                tzs.add(x["ts"][-6:])
print("  qc151_fields ts 时区集合：%s" % tzs)

print("\n== (d) 带内「快 vs 慢」到底是几倍？按趟中位 ==")
F = [t for t in T if t["live"] >= 28 and 1180 <= t["units0"] <= 1360]
SL = [t for t in T if t["live"] < 28 and 1180 <= t["units0"] <= 1360]
print("  fast 趟 %d（units0 %s）中位 live %.2f" % (len(F), sorted(t["units0"] for t in F),
                                                statistics.median(t["live"] for t in F)))
print("  slow 趟 %d（units0 %s）中位 live %.2f" % (len(SL), sorted(t["units0"] for t in SL),
                                                statistics.median(t["live"] for t in SL)))
sl_hl = [t for t in SL if t["units0"] >= 1340]
print("  其中「重负载慢趟」units0>=1340 的 %d 趟 live=%s → 跨日期极差 %.2fx" % (
    len(sl_hl), sorted(round(t["live"], 2) for t in sl_hl),
    max(t["live"] for t in sl_hl)/min(t["live"] for t in sl_hl)))
