# -*- coding: utf-8 -*-
import glob
import json
import os
import sys

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

json_files = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json")))
print(f"Total measure_w*.json found: {len(json_files)}")

# Check trips
trips = sorted(list({os.path.basename(os.path.dirname(p)) for p in json_files}))
print(f"Total trips with measure_w*.json: {len(trips)}")

# Let's inspect some sample keys from a json file
if json_files:
    sample_file = json_files[0]
    with open(sample_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Sample file: {sample_file}")
    print(f"Keys: {list(data.keys())}")
    if "stats" in data:
        print(f"stats keys: {list(data['stats'].keys())}")
    if "gate" in data:
        print(f"gate keys: {list(data['gate'].keys())}")
    if "counters" in data:
        print(f"counters keys: {list(data['counters'].keys()) if isinstance(data['counters'], dict) else type(data['counters'])}")
