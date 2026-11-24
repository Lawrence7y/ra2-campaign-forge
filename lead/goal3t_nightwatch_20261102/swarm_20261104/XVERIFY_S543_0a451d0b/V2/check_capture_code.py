# -*- coding: utf-8 -*-
HARNESS = r"D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py"

with open(HARNESS, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, l in enumerate(lines):
    if "def capture_frame" in l or "def _capture" in l:
        print(f"--- Line {idx+1} ---")
        for i in range(max(0, idx-2), min(len(lines), idx+40)):
            print(f"{i+1:4d}: {lines[i]}", end="")
        print()
