# -*- coding: utf-8 -*-
"""Inspect launch arguments across v3a, v3b, v4b, v4c, v4d, v4e, ha, hb."""
import json
import os

TRIP_BASE = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

trips = ["l3_20261031ha", "l3_20261031hb", "l3_1101v3a", "l3_1101v3b", "l3_1101v4b", "l3_1101v4c", "l3_1101v4d", "l3_1101v4e"]

for t in trips:
    p = os.path.join(TRIP_BASE, t, "_launch_result.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        argv = d.get("argv", [])
        print(f"\nTrip: {t}")
        print("  harness:", d.get("harness"))
        print("  harness_sha16:", d.get("harness_sha16"))
        for i in range(len(argv)):
            if argv[i].startswith("--h8") or argv[i].startswith("--measure") or argv[i] == "--target-map":
                val = argv[i+1] if i+1 < len(argv) and not argv[i+1].startswith("--") else ""
                print(f"    {argv[i]} = {val}")
