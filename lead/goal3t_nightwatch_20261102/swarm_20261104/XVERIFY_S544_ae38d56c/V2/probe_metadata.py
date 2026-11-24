# -*- coding: utf-8 -*-
"""Probe metadata of all measure_w*.json files in TRIPS."""
import glob
import json
import os

TRIP_DIR = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

sample_trips = ["l3_1101v4e", "l3_1101v4d", "l3_20261021", "l3_20261031ha", "archive_T38"]
for st in sample_trips:
    td = os.path.join(TRIP_DIR, st)
    if os.path.exists(td):
        # Check qc151_fields.json
        qf = os.path.join(td, "qc151_fields.json")
        if os.path.exists(qf):
            with open(qf, "r", encoding="utf-8") as f:
                qd = json.load(f)
            print(f"\nTrip {st} qc151_fields type: {type(qd)}")
            if isinstance(qd, list):
                print(f"  first item in list: {qd[0] if qd else None}")
            elif isinstance(qd, dict):
                print(f"  keys: {list(qd.keys())[:10]}")
        
        # Check if there are other files with timestamps
        for f in os.listdir(td):
            if "time" in f.lower() or "gate" in f.lower() or "judge" in f.lower() or f.endswith(".json") or f.endswith(".txt"):
                if f.startswith("rec_") or f.startswith("except_post_") or f.startswith("judge_"):
                    print(f"  file with date/time: {f}")
