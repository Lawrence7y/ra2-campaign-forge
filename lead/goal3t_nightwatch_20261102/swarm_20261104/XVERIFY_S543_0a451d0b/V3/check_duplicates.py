# -*- coding: utf-8 -*-
import os
import glob
import hashlib
from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

dup_group1 = [
    os.path.join(BASE, "archive_T33", "measure_w2_end_x.png"),
    os.path.join(BASE, "archive_T42", "measure_w1_end_x.png"),
    os.path.join(BASE, "archive_T42", "measure_w2_end_x.png"),
    os.path.join(BASE, "archive_T45", "measure_w2_end_x.png"),
]

dup_group2 = [
    os.path.join(BASE, "archive_T36", "measure_w1_end_x.png"),
    os.path.join(BASE, "archive_T38", "measure_w1_end_x.png"),
]

print("=== Checking dup_group1 ===")
for p in dup_group1:
    exists = os.path.exists(p)
    if exists:
        raw_sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
        im = Image.open(p)
        px_sha = hashlib.sha256(im.convert("RGB").tobytes()).hexdigest()
        stat = os.stat(p)
        print(f"{os.path.relpath(p, BASE):35s} size={stat.st_size} raw_sha={raw_sha[:16]} px_sha={px_sha[:16]} mtime={stat.st_mtime}")

print("\n=== Checking dup_group2 ===")
for p in dup_group2:
    exists = os.path.exists(p)
    if exists:
        raw_sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
        im = Image.open(p)
        px_sha = hashlib.sha256(im.convert("RGB").tobytes()).hexdigest()
        stat = os.stat(p)
        print(f"{os.path.relpath(p, BASE):35s} size={stat.st_size} raw_sha={raw_sha[:16]} px_sha={px_sha[:16]} mtime={stat.st_mtime}")
