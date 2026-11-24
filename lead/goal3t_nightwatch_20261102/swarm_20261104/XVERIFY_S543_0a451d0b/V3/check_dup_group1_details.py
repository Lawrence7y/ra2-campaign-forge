# -*- coding: utf-8 -*-
import json
import os
from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

paths = [
    ("archive_T33", "w2", "measure_w2_end_x.png"),
    ("archive_T42", "w1", "measure_w1_end_x.png"),
    ("archive_T42", "w2", "measure_w2_end_x.png"),
    ("archive_T45", "w2", "measure_w2_end_x.png"),
]

for trip, w_name, png_name in paths:
    qpath = os.path.join(BASE, trip, "qc151_fields.json")
    with open(qpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    forensics = [r for r in data if r.get("key") == f"measure_forensics_{w_name}"]
    print(trip, w_name, forensics[0]["value"] if forensics else "NOT FOUND")

# Also let's check what this image actually depicts
p = os.path.join(BASE, "archive_T33", "measure_w2_end_x.png")
im = Image.open(p)
print(f"\nImage info: size={im.size}, mode={im.mode}")
# Let's inspect some sample pixels or bounding boxes
# In S543 line 153, it says: "是纯战斗画面·无面板"
