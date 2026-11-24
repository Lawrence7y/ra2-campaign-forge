# -*- coding: utf-8 -*-
"""§540 -- 29 窗冻结时刻普查（补 §539 的最大缺口）与 w0 内部冻结定位。

只读 measure_w*.json。零真机、零写入。

对每个「有推进」的窗，定位**最后一个帧沿的时刻**（= 该窗内冻结起点）；
若该窗 df>0 且随后同趟还有 df==0 的窗，则该时刻即整趟的冻结起点。
"""
import glob
import json
import os

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

trips = {}
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json"))):
    j = json.load(open(p, encoding="utf-8"))
    ed = j.get("frame_edges") or []
    if not ed:
        continue
    trip = os.path.basename(os.path.dirname(p))
    trips.setdefault(trip, []).append({
        "win": j.get("window"),
        "ed": ed,
        "span": j.get("span_s") or 0.0,
        "f0": ed[0][0],
        "f1": ed[-1][0],
        "n": len(ed),
        "t_abs0": j.get("t_abs0"),
        "max_stall": (j.get("stats") or {}).get("max_stall_s"),
        "units0": (j.get("gate") or {}).get("units0"),
    })

print("trips: %d" % len(trips))
print()

# 找出有 df==0 窗的趟
frozen_trips = [t for t, ws in trips.items()
                if any(w["f0"] != 0 and w["f0"] == w["f1"] for w in ws)]
print("含战斗段冻结窗的趟: %d -> %s" % (len(frozen_trips), sorted(frozen_trips)))
print()

print("=" * 108)
print("★ 每个冻结趟：冻结起点定位（最后一个帧沿）+ 各窗 f0/f1")
print("=" * 108)
print("%-18s %-6s %-14s %-10s %-10s %s" % (
    "trip", "units0", "w0 帧区间", "w0末沿t", "冻结起点", "各窗"))

results = []
for t in sorted(frozen_trips):
    ws = sorted(trips[t], key=lambda x: x["win"])
    line = []
    for w in ws:
        line.append("w%s[%d,%d]" % (w["win"], w["f0"], w["f1"]))
    # 找最后一个有推进的窗
    advancing = [w for w in ws if w["f1"] != w["f0"]]
    if advancing:
        lastadv = max(advancing, key=lambda x: x["win"])
        ed = lastadv["ed"]
        t0 = ed[0][1]
        last_t = ed[-1][1] - t0
        span = lastadv["span"]
        fz_t = "w%s@%.2fs/%.1fs" % (lastadv["win"], last_t, span)
        adv_win = "w%s[%d,%d]" % (lastadv["win"], lastadv["f0"], lastadv["f1"])
    else:
        fz_t = "(整趟无推进)"
        adv_win = "-"
        last_t = None
    print("%-18s %-6s %-14s %-10s %-10s %s" % (
        t[:18], ws[0]["units0"], adv_win,
        ("%.2fs" % last_t) if last_t is not None else "-",
        fz_t, " ".join(line)))
    results.append((t, ws[0]["units0"], last_t, ws))

print()
print("=" * 108)
print("★ 冻结起点 t 的分布（只在有推进窗的末沿）")
print("=" * 108)
ts = sorted(r[2] for r in results if r[2] is not None)
print("  取值: %s" % ["%.2f" % x for x in ts])
if ts:
    print("  min=%.2f max=%.2f 中位=%.2f" % (ts[0], ts[-1], ts[len(ts) // 2]))

print()
print("=" * 108)
print("★ 逐趟：w0 的内部形态（df>0 但有长停滞的，冻结在窗内）")
print("=" * 108)
for t in sorted(frozen_trips):
    ws = sorted(trips[t], key=lambda x: x["win"])
    w0 = ws[0]
    ed = w0["ed"]
    df = w0["f1"] - w0["f0"]
    ms = w0["max_stall"]
    if isinstance(ms, (int, float)) and ms >= 1.0:
        t0 = ed[0][1]
        last_t = ed[-1][1] - t0
        print("  %-18s w0 df=%-4d span=%-5.2f max_stall=%6.3f 末沿t=%6.2f  => 窗内冻结 %.2fs" % (
            t[:18], df, w0["span"], ms, last_t, w0["span"] - last_t))
