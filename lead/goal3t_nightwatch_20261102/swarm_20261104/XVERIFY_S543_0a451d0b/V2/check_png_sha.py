# -*- coding: utf-8 -*-
import hashlib
import os

HARNESS = r"D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py"
BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

# Read harness around screenshot
if os.path.exists(HARNESS):
    with open(HARNESS, "r", encoding="utf-8") as f:
        lines = f.readlines()
    print(f"Harness total lines: {len(lines)}")
    # Find forensics or measure_w
    for idx, l in enumerate(lines):
        if "_measure_window_forensics" in l or "measure_w" in l and "png" in l:
            start = max(0, idx - 5)
            end = min(len(lines), idx + 35)
            print(f"--- Harness lines {start+1}..{end} ---")
            for i in range(start, end):
                print(f"{i+1:4d}: {lines[i]}", end="")
            break

# Check files with sha 2f5ddc60
targets = [
    os.path.join(BASE, "archive_T33", "measure_w2_end_x.png"),
    os.path.join(BASE, "archive_T42", "measure_w1_end_x.png"),
    os.path.join(BASE, "archive_T42", "measure_w2_end_x.png"),
    os.path.join(BASE, "archive_T45", "measure_w2_end_x.png"),
]

for t in targets:
    if os.path.exists(t):
        size = os.path.getsize(t)
        mtime = os.path.getmtime(t)
        with open(t, "rb") as fp:
            data = fp.read()
        sha = hashlib.sha256(data).hexdigest()
        print(f"File: {t}\n  size: {size}, mtime: {mtime}, sha256: {sha}")
