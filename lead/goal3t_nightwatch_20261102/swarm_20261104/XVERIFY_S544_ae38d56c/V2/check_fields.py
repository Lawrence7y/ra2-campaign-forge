import os
import json

TRIPS = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

trips = ["l3_1101v3a", "l3_1101v3b", "l3_1101v4c", "l3_1101v4d", "l3_1101v4e", "l3_20261031ha", "l3_20261031hb", "l1c_20261021", "l3_20261021"]

for t in trips:
    p = os.path.join(TRIPS, t, "qc151_fields.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as fp:
            d = json.load(fp)
        keys = [k for k in d.keys() if "start_frame" in k or "measure" in k or "frame" in k]
        print(f"{t}:")
        for k in keys:
            print(f"  {k} = {d[k]}")
    else:
        print(f"{t}: no qc151_fields.json")
