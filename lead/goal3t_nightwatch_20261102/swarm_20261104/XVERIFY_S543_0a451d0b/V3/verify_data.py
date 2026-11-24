# -*- coding: utf-8 -*-
import os
import glob
import json
import hashlib
from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

print("BASE exists:", os.path.exists(BASE))

# 1. Check all measure_w*.json
json_files = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json")))
print(f"Total measure_w*.json files: {len(json_files)}")

trips = set()
valid_wins = []
no_edges = []
for p in json_files:
    trip = os.path.basename(os.path.dirname(p))
    trips.add(trip)
    try:
        with open(p, "r", encoding="utf-8") as f:
            j = json.load(f)
    except Exception as e:
        print(f"Error loading {p}: {e}")
        continue
    edges = j.get("frame_edges") or []
    w = j.get("window")
    stats = j.get("stats") or {}
    fps_avg = stats.get("fps_avg")
    if not edges:
        no_edges.append((trip, w, p))
        continue
    f0 = edges[0][0]
    f1 = edges[-1][0]
    df = f1 - f0
    dur = edges[-1][1] - edges[0][1]
    span = j.get("span_s") or 0.0
    valid_wins.append({
        "trip": trip,
        "w": w,
        "f0": f0,
        "f1": f1,
        "df": df,
        "span": span,
        "dur": dur,
        "fps_avg": fps_avg,
        "path": p,
        "dir": os.path.dirname(p)
    })

print(f"Valid windows with frame_edges: {len(valid_wins)}")
print(f"Windows with NO frame_edges: {len(no_edges)}")
for x in no_edges:
    print("  no edges:", x)

adv = [w for w in valid_wins if w["df"] > 0]
frz29 = [w for w in valid_wins if w["df"] == 0 and w["f0"] != 0]
loadfrz = [w for w in valid_wins if w["df"] == 0 and w["f0"] == 0]
neg = [w for w in valid_wins if w["df"] < 0]

print(f"Classification: df>0: {len(adv)}, df==0 & f0!=0: {len(frz29)}, df==0 & f0==0: {len(loadfrz)}, df<0: {len(neg)}")

healthy = [w for w in adv if (w["fps_avg"] or 0) >= 28]
slow = [w for w in adv if (w["fps_avg"] or 0) < 28]
print(f"In df>0 (63 windows): fps_avg >= 28: {len(healthy)}, fps_avg < 28: {len(slow)}")

# 2. Check png files in trips
all_end_pngs = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png")))
print(f"Total measure_w*_end_*.png files: {len(all_end_pngs)}")
for p in all_end_pngs:
    print("  end png:", os.path.relpath(p, BASE))
