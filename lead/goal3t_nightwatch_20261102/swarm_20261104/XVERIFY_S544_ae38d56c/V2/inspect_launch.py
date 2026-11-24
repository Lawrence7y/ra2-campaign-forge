# -*- coding: utf-8 -*-
"""Inspect launch results, maps, and argv of all relevant trips."""
import json
import os

TRIP_BASE = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

trips_to_check = [
    "l1c_20261021", "l1d_20261021", "l1e_20261021", "l3_20261021",
    "l1_20261023hb", "l1_20261023e4", "l3_20261023q", "l3_20261023r",
    "l3_20261031ha", "l3_20261031hb",
    "l3_1101v3a", "l3_1101v3b",
    "l3_1101v4c", "l3_1101v4d", "l3_1101v4e",
    "archive_T38"
]

for t in trips_to_check:
    td = os.path.join(TRIP_BASE, t)
    lr = os.path.join(td, "_launch_result.json")
    print("=" * 80)
    print("TRIP:", t)
    if os.path.exists(lr):
        with open(lr, "r", encoding="utf-8") as f:
            d = json.load(f)
        print("  harness:", d.get("harness"))
        print("  harness_sha16:", d.get("harness_sha16"))
        print("  argv:", d.get("argv"))
    else:
        print("  _launch_result.json NOT FOUND")
        # Check qc151_fields.json
        qf = os.path.join(td, "qc151_fields.json")
        if os.path.exists(qf):
            with open(qf, "r", encoding="utf-8") as f:
                qd = json.load(f)
            h = [x for x in qd if x.get("key") in ("harness", "harness_sha16", "argv", "target_map", "map_sha256")]
            print("  qc151_fields relevant:", h)
