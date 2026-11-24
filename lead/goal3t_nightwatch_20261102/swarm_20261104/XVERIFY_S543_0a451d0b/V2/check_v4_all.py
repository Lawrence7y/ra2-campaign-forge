# -*- coding: utf-8 -*-
import glob
import json
import os

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

for t in ["l3_1101v4a", "l3_1101v4b", "l3_1101v4c", "l3_1101v4d", "l3_1101v4e"]:
    tdir = os.path.join(BASE, t)
    for p in sorted(glob.glob(os.path.join(tdir, "measure_w*.json"))):
        with open(p, "r", encoding="utf-8") as f:
            j = json.load(f)
        ed = j.get("frame_edges") or []
        stats = j.get("stats") or {}
        print(f"{t} {os.path.basename(p)}: edges={len(ed)}, df={ed[-1][0]-ed[0][0] if ed else None}, fps_avg={stats.get('fps_avg')}")
