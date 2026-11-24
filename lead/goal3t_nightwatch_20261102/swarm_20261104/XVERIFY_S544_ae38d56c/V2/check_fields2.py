import os
import json

TRIPS = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

trips = ["l3_1101v3a", "l3_1101v4d"]

for t in trips:
    p = os.path.join(TRIPS, t, "qc151_fields.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as fp:
            d = json.load(fp)
        print(f"{t}: type={type(d)}, len={len(d) if isinstance(d, list) else None}")
        if isinstance(d, list):
            for item in d[:5]:
                print("  item:", item)
