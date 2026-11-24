# -*- coding: utf-8 -*-
import glob
import json
import os
import sys

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

json_files = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json")))

all_records = []
skipped = []

for p in json_files:
    trip = os.path.basename(os.path.dirname(p))
    fname = os.path.basename(p)
    try:
        with open(p, "r", encoding="utf-8") as f:
            j = json.load(f)
    except Exception as e:
        skipped.append((trip, fname, f"json load error: {e}"))
        continue

    ed = j.get("frame_edges") or []
    if not ed:
        skipped.append((trip, fname, f"no frame_edges or empty: {len(ed)}"))
        continue

    f0 = ed[0][0]
    f1 = ed[-1][0]
    t0 = ed[0][1]
    t1 = ed[-1][1]
    df = f1 - f0
    dur = t1 - t0

    w = j.get("window")
    span_s = j.get("span_s") or 0.0
    stats = j.get("stats") or {}
    fps_avg = stats.get("fps_avg")
    logic_frames = stats.get("logic_frames")
    max_stall_s = stats.get("max_stall_s")

    gate = j.get("gate") or {}
    pre_fps15 = gate.get("pre_fps15")
    gate_ok = gate.get("ok")

    counters = j.get("counters") or []
    
    # Analyze counters stability
    # Check what counters structure looks like
    c_units = []
    c_g = []
    c_b = []
    if isinstance(counters, list):
        for c in counters:
            # c could be a dict or list
            if isinstance(c, dict):
                c_units.append(c.get("units"))
                c_g.append(c.get("g"))
                c_b.append(c.get("b"))
            elif isinstance(c, (list, tuple)) and len(c) >= 4:
                # [t, units, g, b] or similar? Let's check structure
                pass

    all_records.append({
        "path": p,
        "trip": trip,
        "fname": fname,
        "window": w,
        "f0": f0,
        "f1": f1,
        "df": df,
        "dur": dur,
        "span_s": span_s,
        "fps_avg": fps_avg,
        "logic_frames": logic_frames,
        "max_stall_s": max_stall_s,
        "pre_fps15": pre_fps15,
        "gate_ok": gate_ok,
        "counters_len": len(counters),
        "raw_json": j
    })

print(f"Total files: {len(json_files)}")
print(f"Skipped files: {len(skipped)}")
for s in skipped:
    print(f"  Skipped: {s[0]}/{s[1]} - {s[2]}")
print(f"Valid records with frame_edges: {len(all_records)}")
trips_valid = {r['trip'] for r in all_records}
print(f"Unique trips with valid frame_edges: {len(trips_valid)}")
