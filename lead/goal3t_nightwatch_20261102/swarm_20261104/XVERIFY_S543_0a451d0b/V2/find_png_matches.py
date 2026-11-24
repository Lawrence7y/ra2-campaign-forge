# -*- coding: utf-8 -*-
import glob
import hashlib
import os

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

target_sha = "f61c9808dabd3aefcbdeaeb8e021564f3e4f310512a6bec539c24ed4c526f94b"

matches = []
for p in glob.glob(os.path.join(BASE, "*", "*.png")):
    with open(p, "rb") as fp:
        sha = hashlib.sha256(fp.read()).hexdigest()
    if sha == target_sha:
        matches.append(p)

print(f"Total files matching {target_sha[:8]}: {len(matches)}")
for m in matches:
    print(" ", m)
