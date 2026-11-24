# -*- coding: utf-8 -*-
import glob
import json
import os

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

all_files = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json")))

adv_records = []
for p in all_files:
    try:
        with open(p, "r", encoding="utf-8") as f:
            j = json.load(f)
    except Exception:
        continue
    ed = j.get("frame_edges") or []
    if not ed:
        continue
    f0, f1 = ed[0][0], ed[-1][0]
    df = f1 - f0
    if df > 0:
        trip = os.path.basename(os.path.dirname(p))
        w = j.get("window")
        stats = j.get("stats") or {}
        fps_avg = stats.get("fps_avg")
        span_s = j.get("span_s")
        adv_records.append({
            "trip": trip,
            "window": w,
            "fps_avg": fps_avg,
            "df": df,
            "f0": f0,
            "f1": f1,
            "span_s": span_s
        })

fast = [r for r in adv_records if (r["fps_avg"] or 0) >= 28.0]
slow = [r for r in adv_records if (r["fps_avg"] or 0) < 28.0]

print(f"Total advancing windows: {len(adv_records)}")
print(f"fps_avg >= 28: {len(fast)}")
print(f"fps_avg < 28: {len(slow)}")

print("\n--- All 38 slow windows (< 28 fps) ---")
print(f"{'No.':<4} {'Trip':<25} {'Win':<4} {'fps_avg':<10} {'df':<6} {'f0':<6} {'f1':<6} {'span_s':<6}")
for idx, r in enumerate(slow, 1):
    fps_str = f"{r['fps_avg']:.4f}" if r['fps_avg'] is not None else "None"
    print(f"{idx:<4} {r['trip']:<25} w{r['window']:<3} {fps_str:<10} {r['df']:<6} {r['f0']:<6} {r['f1']:<6} {r['span_s']:<6}")
