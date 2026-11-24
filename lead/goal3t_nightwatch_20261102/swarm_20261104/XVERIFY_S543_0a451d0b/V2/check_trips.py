# -*- coding: utf-8 -*-
import glob
import json
import os

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

trips = sorted(os.listdir(BASE))
print("All trips in BASE:")
for t in trips:
    if "v4" in t:
        print("  v4 trip:", t)
