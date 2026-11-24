# -*- coding: utf-8 -*-
"""§544 目标①「慢窗」构成拆解：把每个有推进窗按「终局截断 / 全程慢 / 健康」分型。

只读真机数据（measure_w*.json）。零真机、零写入母本。只打 stdout，不写文件。

分型定义（窗内，逻辑帧沿序列）：
  末段停滞 tail = 采样末时刻 - 末沿时刻
  TRUNC   : tail/span >= 0.5            ⇒ 游戏在窗中途停摆（结算/死机/卡住）
  SLOW    : tail/span <  0.5 且 fps<28  ⇒ 全程推进但整体慢 = 目标①真候选
  HEALTHY : tail/span <  0.5 且 fps>=28
另算每份 json 的采样缺口（samples.t 的 dt>10ms 累计）作为宿主争用指纹。
"""
import glob
import json
import os
import statistics
from collections import Counter

TRIP = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

files = sorted(glob.glob(os.path.join(TRIP, "*", "measure_w*.json")))
files += sorted(glob.glob(os.path.join(TRIP, "measure_w*.json")))

rows = []
for p in files:
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        print("READ_FAIL", p, e)
        continue
    trip = d.get("trip_id") or "?"
    edges = d.get("frame_edges") or []
    span = d.get("span_s") or 0.0
    stats = d.get("stats") or {}
    gate = d.get("gate") or {}
    s = d.get("samples") or {}
    t = s.get("t") or []

    gap_sum = 0.0
    gap_n = 0
    for i in range(len(t) - 1):
        dt = t[i + 1] - t[i]
        if dt > 0.010:
            gap_n += 1
            gap_sum += dt

    rel = os.path.relpath(p, TRIP).replace("\\", "/")
    rec = dict(
        name=rel, trip=trip, span=span, n_edges=len(edges),
        fps=stats.get("fps_avg"), units0=gate.get("units0"), gate_ok=gate.get("ok"),
        verdict=d.get("verdict"), gap_s=round(gap_sum, 3), gap_n=gap_n,
        f0=None, f1=None, df=None, tail=None, tf=None,
    )

    if len(edges) >= 2:
        rec["f0"] = edges[0][0]
        rec["f1"] = edges[-1][0]
        rec["df"] = rec["f1"] - rec["f0"]
        rec["tail"] = round(t[-1] - edges[-1][1], 3) if t else None
        rec["tf"] = round(rec["tail"] / span, 3) if (rec["tail"] is not None and span) else None
    elif len(edges) == 1:
        rec["f0"] = edges[0][0]
        rec["f1"] = edges[0][0]
        rec["df"] = 0
        rec["tail"] = span
        rec["tf"] = 1.0
    rows.append(rec)

for r in rows:
    if r["df"] is None:
        r["cls"] = "NO_EDGES"
    elif r["df"] < 0:
        r["cls"] = "BACK"
    elif r["df"] == 0:
        r["cls"] = "LOAD" if r["f0"] == 0 else "FROZEN"
    elif (r["tf"] or 0.0) >= 0.5:
        r["cls"] = "TRUNC"
    elif (r["fps"] or 0) < 28:
        r["cls"] = "SLOW"
    else:
        r["cls"] = "HEALTHY"

c = Counter(r["cls"] for r in rows)
print("=== 全量 %d 份 json ===" % len(rows))
for k in sorted(c, key=lambda x: -c[x]):
    print("  %-9s %d" % (k, c[k]))

print("\n=== 有推进窗：末段停滞占比分档 ===")
b = Counter()
for r in rows:
    if r["cls"] in ("TRUNC", "SLOW", "HEALTHY"):
        tf = r["tf"] or 0.0
        key = (">=90%" if tf >= 0.9 else "50-90%" if tf >= 0.5 else
               "20-50%" if tf >= 0.2 else "5-20%" if tf >= 0.05 else "<5%")
        b[key] += 1
for k in ["<5%", "5-20%", "20-50%", "50-90%", ">=90%"]:
    print("  tail %-7s %d" % (k, b[k]))

print("\n=== SLOW（tail<50% 且 fps<28）= 目标①真候选 ===")
slow = [r for r in rows if r["cls"] == "SLOW"]
print("  计数 %d" % len(slow))
if slow:
    print("  %-30s %6s %6s %6s %7s %5s %7s %5s" % ("name", "fps", "df", "tail%", "gap_s", "gapn", "units0", "gate"))
    for r in sorted(slow, key=lambda x: x["fps"] or 0):
        print("  %-30s %6.2f %6d %6.1f %7.2f %5d %7s %5s" % (
            r["name"], r["fps"] or 0, r["df"], 100 * (r["tf"] or 0),
            r["gap_s"], r["gap_n"], r["units0"], r["gate_ok"]))

print("\n=== HEALTHY ===")
h = [r for r in rows if r["cls"] == "HEALTHY"]
if h:
    print("  计数 %d  fps %.2f..%.2f" % (len(h), min(r["fps"] for r in h), max(r["fps"] for r in h)))
else:
    print("  计数 0")

print("\n=== TRUNC（tail>=50% 窗长）清单 ===")
tr = [r for r in rows if r["cls"] == "TRUNC"]
print("  计数 %d" % len(tr))
for r in sorted(tr, key=lambda x: -(x["tf"] or 0)):
    print("  %-30s f %5s->%-5s df %4s tail %6.2fs (%5.1f%%) fps %6.2f gap %6.2f" % (
        r["name"], r["f0"], r["f1"], r["df"], r["tail"] or 0, 100 * (r["tf"] or 0),
        r["fps"] or 0, r["gap_s"]))

print("\n=== 采样缺口分布（dt>10ms 累计）===")
for cls in ["HEALTHY", "SLOW", "TRUNC", "FROZEN"]:
    sub = [r for r in rows if r["cls"] == cls]
    if not sub:
        continue
    gaps = [r["gap_s"] for r in sub]
    print("  %-8s n=%3d  gap>0.5s窗 %3d  max %6.2fs  中位 %6.3fs" % (
        cls, len(sub), sum(1 for g in gaps if g > 0.5), max(gaps), statistics.median(gaps)))
