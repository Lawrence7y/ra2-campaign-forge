# -*- coding: utf-8 -*-
import glob
import json
import os

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

# Check sample counters structure
for p in glob.glob(os.path.join(BASE, "*", "measure_w*.json"))[:5]:
    with open(p, "r", encoding="utf-8") as f:
        j = json.load(f)
    counters = j.get("counters")
    samples = j.get("samples")
    print(p)
    print("  counters type:", type(counters), "len:", len(counters) if counters else 0)
    if counters and len(counters) > 0:
        print("  counter[0]:", counters[0])
    if samples and len(samples) > 0:
        print("  sample[0]:", samples[0])
    break
