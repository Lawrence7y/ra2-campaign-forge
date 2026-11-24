# -*- coding: utf-8 -*-
import hashlib
import os

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

for t in ["archive_T33", "archive_T42", "archive_T45"]:
    tdir = os.path.join(BASE, t)
    for f in sorted(os.listdir(tdir)):
        if f.endswith(".png"):
            p = os.path.join(tdir, f)
            with open(p, "rb") as fp:
                data = fp.read()
            sha = hashlib.sha256(data).hexdigest()
            print(f"{t}/{f}: sha={sha[:8]}, size={len(data)}")
