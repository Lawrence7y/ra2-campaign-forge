# -*- coding: utf-8 -*-
import os

t35_dir = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\archive_T35"
for f in sorted(os.listdir(t35_dir)):
    if "navsig_burst" in f or "measure" in f:
        print(f, os.path.getsize(os.path.join(t35_dir, f)))
