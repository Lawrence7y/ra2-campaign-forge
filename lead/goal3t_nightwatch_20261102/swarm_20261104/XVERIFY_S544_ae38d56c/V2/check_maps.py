import os
import json

TRIPS = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

for t in ["l1c_20261021", "l3_1101v4d", "l3_1101v4e", "l3_20261031hb"]:
    p = os.path.join(TRIPS, t, "measure_w0.json")
    with open(p, "r", encoding="utf-8") as fp:
        d = json.load(fp)
    print(f"{t}: map_sha256 = {d.get('map_sha256')}")
