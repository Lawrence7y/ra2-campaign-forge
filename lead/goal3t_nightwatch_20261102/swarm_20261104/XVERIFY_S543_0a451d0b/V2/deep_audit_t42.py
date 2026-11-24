# -*- coding: utf-8 -*-
import json
import os

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
t42_dir = os.path.join(BASE, "archive_T42")

print("Files in archive_T42:", os.listdir(t42_dir))

# Check T42_console.log
log_path = os.path.join(t42_dir, "T42_console.log")
if os.path.exists(log_path):
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    print(f"T42_console.log lines: {len(lines)}")
    for l in lines[:20]:
        print("  ", l.strip())
    print("  ...")
    for l in lines[-30:]:
        print("  ", l.strip())

# Check qc151_fields.json
f_path = os.path.join(t42_dir, "qc151_fields.json")
if os.path.exists(f_path):
    with open(f_path, "r", encoding="utf-8", errors="ignore") as f:
        data = json.load(f)
    print("qc151_fields.json type:", type(data))
    if isinstance(data, list):
        print("len:", len(data))
        for row in data[:5]:
            print("  ", row)
    elif isinstance(data, dict):
        print("keys:", list(data.keys()))

# Check forensics in measure_w1 and measure_w2
for w in [0, 1, 2]:
    p = os.path.join(t42_dir, f"measure_w{w}.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            j = json.load(f)
        print(f"\n--- T42 measure_w{w}.json ---")
        for k in ["trip_id", "window", "span_s", "t_clock", "t_abs0", "error", "verdict"]:
            print(f"  {k}: {j.get(k)}")
        ed = j.get("frame_edges", [])
        print(f"  edges count: {len(ed)}, f0={ed[0][0] if ed else None}, f1={ed[-1][0] if ed else None}")
        print(f"  t0={ed[0][1] if ed else None}, t1={ed[-1][1] if ed else None}")
        # samples
        samples = j.get("samples", {})
        if isinstance(samples, dict):
            t_s = samples.get("t", [])
            f_s = samples.get("f", [])
            print(f"  samples count: {len(t_s)}, f unique: {set(f_s) if len(set(f_s)) < 10 else f'{len(set(f_s))} unique'}")
