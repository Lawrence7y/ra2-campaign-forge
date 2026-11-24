# -*- coding: utf-8 -*-
"""V2 终判 2：同图同窗内负载（±40）跨版本配对 —— 时代 vs 工具链的可分性。"""
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

rows = []
with open(os.path.join(OUT, "census.csv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["base_tag"] != "mirror":
            continue
        for k in ("live_fps", "units0", "pre_fps15", "span_s", "gap_s"):
            try:
                r[k] = float(r[k])
            except (TypeError, ValueError):
                r[k] = None
        r["ts"] = r["fields_ts_first"] or ""
        rows.append(r)
for r in rows:
    p = os.path.join(TRIPS, r["dir"], "measure_w%s.json" % r["window"]) if r["dir"] != "." \
        else os.path.join(TRIPS, "measure_w%s.json" % r["window"])
    if os.path.exists(p):
        j = json.load(open(p, encoding="utf-8"))
        cs = j.get("counters") or []
        def mean(k):
            v = [c.get(k) for c in cs if isinstance(c.get(k), int)]
            return sum(v) / len(v) if v else None
        for src, dst in (("units", "c_units"), ("infantry", "c_inf"), ("techno", "c_techno"), ("g", "c_g")):
            r[dst] = mean(src)


def hlabel(r):
    if r["harness_sha16"]:
        return r["harness_sha16"]
    ap = r["argv_harness"] or r["harness_path"]
    if ap and "harness3" in os.path.basename(ap):
        return "harness3"
    return "name:" + os.path.basename(ap) if ap else "UNKNOWN"


strict = [r for r in rows if r["verdict"] == "ok" and r["span_s"] == 25.0
          and r["live_fps"] and r["live_fps"] > 0 and r["c_units"] is not None]
L3 = [r for r in strict if (r["map_sha256"] or "").startswith("f3bb0a4e")]

print("=" * 116)
print("AF. L3 图内：窗级配对，|Δc_units|<=40，跨日期（=跨版本/协议）")
print("=" * 116)
pairs = []
for a, b in itertools.combinations(sorted(L3, key=lambda x: (x["ts"], x["window"])), 2):
    if abs(a["c_units"] - b["c_units"]) <= 40 and a["dir"] != b["dir"]:
        ratio = max(a["live_fps"], b["live_fps"]) / min(a["live_fps"], b["live_fps"])
        pairs.append((ratio, a, b))
pairs.sort(reverse=True)
for ratio, a, b in pairs[:14]:
    print("  %.2fx  [%s w%s %s %-16s c_u=%.0f inf=%.0f live=%6.2f pre15=%6.2f gap=%.2f] vs" % (
        ratio, a["ts"][:16], a["window"], hlabel(a)[:14], a["dir"], a["c_units"], a["c_inf"], a["live_fps"],
        a["pre_fps15"] or -1, a["gap_s"] or 0))
    print("        [%s w%s %s %-16s c_u=%.0f inf=%.0f live=%6.2f pre15=%6.2f gap=%.2f]" % (
        b["ts"][:16], b["window"], hlabel(b)[:14], b["dir"], b["c_units"], b["c_inf"], b["live_fps"],
        b["pre_fps15"] or -1, b["gap_s"] or 0))
print("  共 %d 对；最大 %.2fx；最小 %.2fx" % (len(pairs), pairs[0][0], pairs[-1][0]) if pairs else "  无")
vers_differ = sum(1 for _, a, b in pairs if hlabel(a) != hlabel(b))
print("  其中跨版本的对：%d / %d" % (vers_differ, len(pairs)))

print("\n" + "=" * 116)
print("AG. 固定版本 38244(v4)+sf=800 内部，跨场次（11-01 09:43 / 11-01 16:47 / 11-03 11:19）同窗序同负载对照")
print("=" * 116)
v4 = defaultdict(dict)
for r in L3:
    if hlabel(r) == "38244d2907e7f7fa":
        v4[r["dir"]][int(r["window"])] = r
for w in (0, 1, 2):
    cells = []
    for d in sorted(v4, key=lambda x: v4[x][w]["ts"] if w in v4[x] else ""):
        if w in v4[d]:
            r = v4[d][w]
            cells.append("%s %s c_u=%.0f inf=%.0f live=%6.2f" % (r["ts"][5:16], d, r["c_units"], r["c_inf"], r["live_fps"]))
    print("  w%s: %s" % (w, "   |   ".join(cells)))
    lvs = [v4[d][w]["live_fps"] for d in v4 if w in v4[d]]
    if len(lvs) >= 2:
        print("      w%s 跨场倍率 max/min = %.3f" % (w, max(lvs) / min(lvs)))

print("\n" + "=" * 116)
print("AH. 采样饥饿指纹（samples.t dt>10ms 累计）与 live / 版本 的关系")
print("=" * 116)
hv = defaultdict(lambda: [[], [], []])
for r in strict:
    k = hlabel(r)
    hv[k][0].append(r["live_fps"])
    hv[k][1].append(r["gap_s"] or 0)
    hv[k][2].append(r["units0"])
for k, v in sorted(hv.items(), key=lambda x: min(r["ts"] for r in strict if hlabel(r) == x[0])):
    print("  %-24s live中位 %6.2f  gap_s 中位 %6.3f  max %6.3f  units0 %s" % (
        k[:24], statistics.median(v[0]), statistics.median(v[1]), max(v[1]),
        sorted(set(int(x) for x in v[2] if x is not None))))

print("\n  同版本内 gap>0.5s 的窗 vs 无缺口窗 的 live：")
g1 = [r for r in strict if (r["gap_s"] or 0) > 0.5]
g0 = [r for r in strict if (r["gap_s"] or 0) <= 0.5]
print("    有宿主缺口 n=%d live %s" % (len(g1), sorted(set(r["dir"] for r in g1))))
print("    无缺口     n=%d live 中位 %.2f" % (len(g0), statistics.median([r["live_fps"] for r in g0])))
if g1:
    print("    有缺口     n=%d live 中位 %.2f" % (len(g1), statistics.median([r["live_fps"] for r in g1])))

print("\n" + "=" * 116)
print("AI. §544 引用的「units≈881 在 10-21 拿 9.2」是否落在 1180-1360 带内 + 地图是否同一张")
print("=" * 116)
for d in ("l1c_20261021", "l3_1101v4d", "l3_1101v4e", "l3_20261031hb", "l3_20261021"):
    rs = [r for r in rows if r["dir"] == d]
    r = rs[0]
    cpath = os.path.join(TRIPS, d, "carrier_creation_receipt.json")
    ncar = json.load(open(cpath, encoding="utf-8")).get("files_copied") if os.path.exists(cpath) else "-"
    wins = " ".join("%.2f" % x["live_fps"] for x in sorted(rs, key=lambda y: int(y["window"])) if x["live_fps"])
    print("  %-16s units0=%-6s map=%s 载体件数=%s live(逐窗)=%s" % (
        d, int(r["units0"]) if r["units0"] is not None else "-", (r["map_sha256"] or "")[:12], ncar, wins))

print("\n" + "=" * 116)
print("AJ. 同一 trip 内窗间一致性（fast 趟）：证实「整趟锁定」")
print("=" * 116)
bytrip = defaultdict(list)
for r in strict:
    bytrip[r["dir"]].append(r)
for d, rs in sorted(bytrip.items(), key=lambda x: statistics.median([r["live_fps"] for r in x[1]])):
    if len(rs) < 3:
        continue
    ls = sorted(r["live_fps"] for r in rs)
    print("  %-18s %-10s %-20s live %6.2f %6.2f %6.2f  极差 %5.2f (%.2fx)" % (
        d, rs[0]["ts"][:10], hlabel(rs[0])[:20], ls[0], ls[1], ls[-1], ls[-1] - ls[0], ls[-1] / ls[0]))
