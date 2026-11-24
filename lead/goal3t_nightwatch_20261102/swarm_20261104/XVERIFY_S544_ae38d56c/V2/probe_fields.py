# -*- coding: utf-8 -*-
"""Inspect all 103 measure files."""
import glob
import json
import os

TRIP_DIR = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

sub_files = sorted(glob.glob(os.path.join(TRIP_DIR, "*", "measure_w*.json")))
root_files = sorted(glob.glob(os.path.join(TRIP_DIR, "measure_w*.json")))
all_files = sub_files + root_files

print(f"Total files: {len(all_files)}")

# Let's inspect fields of measure_w*.json
fields_summary = set()
for p in all_files:
    try:
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        fields_summary.update(d.keys())
    except Exception as e:
        print("Error reading", p, e)

print("All keys across all measure files:", sorted(fields_summary))
