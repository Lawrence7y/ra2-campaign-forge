# -*- coding: utf-8 -*-
import os

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

for t in ["archive_T33", "archive_T36", "archive_T38", "archive_T42", "archive_T45"]:
    d = os.path.join(BASE, t)
    for fname in os.listdir(d):
        if fname.endswith(".json") or fname.endswith(".png"):
            p = os.path.join(d, fname)
            st = os.stat(p)
            print(f"{t:15s} {fname:25s} size={st.st_size:8d} mtime={st.st_mtime}")
