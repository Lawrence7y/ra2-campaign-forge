# -*- coding: utf-8 -*-
"""V2 补充：带内各趟的采样相位（首帧号）、载体件数、精确同负载跨日期配对存在性。"""
import csv
import json
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
        for k in ("live_fps", "units0", "pre_fps15", "span_s"):
            try:
                r[k] = float(r[k])
            except (TypeError, ValueError):
                r[k] = None
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

FLAG = ["--h7-measure-start-frame", "--h8-wait-trace", "--h8-wait-hz", "--h7-keep-rect-wait"]
print("=" * 118)
print("L. 带内 1180-1360：相位（实测首帧/末帧）× 协议 × 版本 × 负载 × 载体")
print("=" * 118)
band = {d: rs for d, rs in trip.items() if 1180 <= rs[0]["units0"] <= 1360}
print("%-18s %-19s %-20s %-6s %6s %-14s %-14s %-9s %s" % (
    "dir", "ts", "harness", "sf旗标", "units0", "首窗首帧-末窗末帧", "窗内units 首→末", "载体件数", "live 逐窗"))
for d, rs in sorted(band.items(), key=lambda x: x[1][0]["ts"]):
    argv = json.load(open(os.path.join(TRIPS, d, "_launch_result.json"), encoding="utf-8")).get("argv") or []
    sf = "-"
    for i, a in enumerate(argv):
        if a == "--h7-measure-start-frame":
            sf = argv[i + 1]
    rec = os.path.join(TRIPS, d, "carrier_creation_receipt.json")
    ncar = "-"
    if os.path.exists(rec):
        cj = json.load(open(rec, encoding="utf-8"))
        ncar = "%s/copied=%s/req=%s" % (len(cj.get("files") or {}), cj.get("files_copied"), cj.get("files_requested"))
    seq = sorted(rs, key=lambda x: int(x["window"]))
    f_lo = seq[0]["f0"]
    f_hi = seq[-1]["f1"]
    u_first = u_last = "-"
    j0 = json.load(open(os.path.join(TRIPS, d, "measure_w%s.json" % seq[0]["window"]), encoding="utf-8"))
    cs = j0.get("counters") or []
    uv = [c.get("units") for c in cs if isinstance(c.get("units"), int)]
    if uv:
        u_first, u_last = uv[0], uv[-1]
    jl = json.load(open(os.path.join(TRIPS, d, "measure_w%s.json" % seq[-1]["window"]), encoding="utf-8"))
    uv2 = [c.get("units") for c in (jl.get("counters") or []) if isinstance(c.get("units"), int)]
    tail_last = uv2[-1] if uv2 else "-"
    print("%-18s %-19s %-20s %-6s %6d %-14s %-14s %-9s %s" % (
        d, rs[0]["ts"][:19], hlabel(rs[0])[:20], sf, rs[0]["units0"],
        "%s->%s (跨%d帧)" % (f_lo, f_hi, int(f_hi) - int(f_lo)),
        "%s->%s(末窗%s)" % (u_first, u_last, tail_last), ncar,
        " ".join("w%s:%.2f" % (r["window"], r["live_fps"]) for r in seq)))

print("\n" + "=" * 118)
print("M. 精确同 units0 跨日期对照：全库严格窗里，同一个 units0 值在两个不同日期出现的次数")
print("=" * 118)
g = defaultdict(set)
for r in strict:
    g[int(r["units0"])].add(r["ts"][:10])
multi = {u: sorted(v) for u, v in g.items() if len(v) >= 2}
print("  跨 >=2 个日期的 units0 精确值：%s" % (multi if multi else "无（0 个）"))
print("  ⇒ 「同负载跨时段」在 units0 精确口径下没有任何一对真对照")

print("\n  ±20 容差下的跨日期对照：")
pairs = []
us = sorted(g)
for i, a in enumerate(us):
    for b in us[i + 1:]:
        if b - a <= 20 and (g[a] & g[b]) == set() and (g[a] | g[b]) and len(g[a] | g[b]) >= 2:
            pairs.append((a, b, sorted(g[a]), sorted(g[b])))
print("   %s" % (pairs if pairs else "无"))

print("\n" + "=" * 118)
print("N. 快/慢 与 harness 版本是否 1:1 共线（严格窗，含版本未知组）")
print("=" * 118)
hv = defaultdict(lambda: [0, 0, []])
for r in strict:
    k = hlabel(r)
    i = 0 if r["live_fps"] >= 28 else 1
    hv[k][i] += 1
    hv[k][2].append((int(r["units0"]), round(r["live_fps"], 2), r["ts"][:10]))
for k, v in sorted(hv.items(), key=lambda x: min(t[2] for t in x[1][2])):
    print("  %-30s fast>=28: %2d  slow<28: %2d  (units,live,日期) %s" % (k[:30], v[0], v[1], v[2]))
print("  ⇒ 每个版本内部既出现过快窗也出现过慢窗？")
for k, v in hv.items():
    print("     %-30s %s" % (k[:30], "两态皆有" if v[0] and v[1] else "单态"))

print("\n" + "=" * 118)
print("O. 版本 × 日期 × 负载水平（每版本跑在什么负载上）")
print("=" * 118)
hv2 = defaultdict(lambda: defaultdict(set))
for r in strict:
    hv2[hlabel(r)][r["ts"][:10]].add(int(r["units0"]))
for k, v in sorted(hv2.items()):
    print("  %-30s %s" % (k[:30], {d: sorted(s) for d, s in sorted(v.items())}))
