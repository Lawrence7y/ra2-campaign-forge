# -*- coding: utf-8 -*-
import json

p = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\archive_T32\measure_w0.json"
with open(p, "r", encoding="utf-8") as f:
    j = json.load(f)

print("samples keys:", list(j.get("samples", {}).keys()) if isinstance(j.get("samples"), dict) else type(j.get("samples")))
print("counters length:", len(j.get("counters", [])))
print("counters[0]:", j.get("counters", [])[0])
print("counters[-1]:", j.get("counters", [])[-1])
