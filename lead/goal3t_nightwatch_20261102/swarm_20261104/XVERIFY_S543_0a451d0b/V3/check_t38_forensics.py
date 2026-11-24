# -*- coding: utf-8 -*-
import json
import os

p = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\archive_T38\qc151_fields.json"
with open(p, "r", encoding="utf-8") as f:
    data = json.load(f)

for row in data:
    if "measure_forensics" in row.get("key", ""):
        print(row["key"], row.get("payload"))
