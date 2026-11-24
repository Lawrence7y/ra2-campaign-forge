# -*- coding: utf-8 -*-
import os
import glob
import json
import hashlib
from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

json_files = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json")))

frz29_set = set()
all_wins = {}

for p in json_files:
    trip = os.path.basename(os.path.dirname(p))
    try:
        with open(p, "r", encoding="utf-8") as f:
            j = json.load(f)
    except Exception:
        continue
    edges = j.get("frame_edges") or []
    w = j.get("window")
    key = f"{trip}/w{w}"
    if not edges:
        all_wins[key] = {"trip": trip, "w": w, "edges": 0, "path": p}
        continue
    f0, f1 = edges[0][0], edges[-1][0]
    df = f1 - f0
    all_wins[key] = {"trip": trip, "w": w, "edges": len(edges), "f0": f0, "f1": f1, "df": df, "path": p}
    if df == 0 and f0 != 0:
        frz29_set.add(key)

print(f"29 frozen windows count: {len(frz29_set)}")
print("29 frozen windows:", sorted(frz29_set))

all_end_pngs = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png")))
print(f"\n25 end png files check against 29 frozen windows:")
png_keys = set()
for p in all_end_pngs:
    trip = os.path.basename(os.path.dirname(p))
    fname = os.path.basename(p)
    # measure_w1_end_x.png -> w1
    w_str = fname.split("_")[1] # "w1"
    key = f"{trip}/{w_str}"
    png_keys.add(key)
    win_info = all_wins.get(key, {})
    is_in_frz29 = key in frz29_set
    print(f"  {key:25s} in_frz29={str(is_in_frz29):5s} df={win_info.get('df')} f0={win_info.get('f0')}")

print("\nFrozen 29 windows WITHOUT end png:")
missing_png = frz29_set - png_keys
for k in sorted(missing_png):
    print("  missing end png:", k, all_wins.get(k))

print("\nEnd png windows NOT in 29 frozen windows:")
not_in_frz29 = png_keys - frz29_set
for k in sorted(not_in_frz29):
    print("  not in frz29:", k, all_wins.get(k))
