# -*- coding: utf-8 -*-
import os
import json

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

trips = [
    ("archive_T33", "measure_w1.json"),
    ("archive_T34", "measure_w1.json"),
    ("archive_T36", "measure_w1.json"),
    ("archive_T38", "measure_w1.json"),
    ("archive_T39", "measure_w2.json"),
    ("archive_T40", "measure_w1.json"),
    ("archive_T41", "measure_w1.json"),
    ("archive_T43", "measure_w1.json"),
    ("archive_T44", "measure_w1.json"),
    ("archive_T45", "measure_w1.json"),
    ("archive_T49_u0800", "measure_w1.json"),
    ("l3_20261023r", "measure_w2.json"),
]

for trip, wjson in trips:
    p = os.path.join(BASE, trip, wjson)
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    edges = data.get("frame_edges", [])
    f_last = edges[-1][0] if edges else None
    print(f"{trip:20s} {wjson:18s} f_first={edges[0][0] if edges else None} f_last={f_last} len_edges={len(edges)}")
