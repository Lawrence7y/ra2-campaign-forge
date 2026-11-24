# -*- coding: utf-8 -*-
"""Task 2: Check harness versions, argv, schema, etc. for all trips."""
import glob
import hashlib
import json
import os
import re

TRIP_BASE = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

with open(r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V2/all_windows.json", "r", encoding="utf-8") as f:
    windows = json.load(f)

# Group by trip_dir
trips = {}
for w in windows:
    td = w["trip_dir"]
    if td not in trips:
        trips[td] = {
            "trip_dir": td,
            "windows": [],
            "dt_str": w["dt_str"],
            "map_sha256": w["map_sha256"],
            "units0": w["units0"],
        }
    trips[td]["windows"].append(w)

print(f"Total distinct trip dirs: {len(trips)}")

for td, tinfo in trips.items():
    pdir = os.path.join(TRIP_BASE, td) if td != "." else TRIP_BASE
    
    # 1. Check measure_w*.json fields
    w0 = tinfo["windows"][0]
    schema = w0.get("schema")
    h8_block = None
    
    # Check measure_w0.json raw
    w0_path = os.path.join(pdir, "measure_w0.json")
    if os.path.exists(w0_path):
        with open(w0_path, "r", encoding="utf-8") as f:
            d = json.load(f)
            h8_block = d.get("h8")
            if not schema:
                schema = d.get("schema")
    
    # 2. Check _launch_result.json
    lr_path = os.path.join(pdir, "_launch_result.json")
    lr_data = {}
    if os.path.exists(lr_path):
        try:
            with open(lr_path, "r", encoding="utf-8") as f:
                lr_data = json.load(f)
        except Exception:
            pass
            
    # 3. Check qc151_fields.json
    qf_path = os.path.join(pdir, "qc151_fields.json")
    qf_data = []
    if os.path.exists(qf_path):
        try:
            with open(qf_path, "r", encoding="utf-8") as f:
                qf_data = json.load(f)
        except Exception:
            pass

    # Extract harness info
    harness_script = lr_data.get("harness")
    harness_sha16 = lr_data.get("harness_sha16") or (h8_block.get("sha16") if h8_block else None)
    argv = lr_data.get("argv")
    if argv and not harness_script:
        harness_script = argv[0]
        
    if isinstance(qf_data, list):
        for item in qf_data:
            k = item.get("key")
            v = item.get("value")
            if k == "harness" and not harness_script:
                harness_script = v
            if k == "harness_sha16" and not harness_sha16:
                harness_sha16 = v

    # Also check if there's any mention in logs or txt files
    judge_files = glob.glob(os.path.join(pdir, "judge_*.txt"))
    judge_info = None
    if judge_files:
        judge_info = os.path.basename(judge_files[0])

    # Calculate average live_fps across computable windows in this trip
    fps_list = [w["live_fps"] for w in tinfo["windows"] if w["live_fps"] is not None and w["live_fps"] > 0]
    mean_live_fps = sum(fps_list) / len(fps_list) if fps_list else None
    
    tinfo["harness_script"] = harness_script
    tinfo["harness_sha16"] = harness_sha16
    tinfo["argv"] = argv
    tinfo["schema"] = schema
    tinfo["mean_live_fps"] = mean_live_fps
    tinfo["computable_wins"] = len(fps_list)
    tinfo["judge_file"] = judge_info

# Let's inspect the results sorted by time
print("\n=== Trip Summary Table ===")
print(f"{'Trip Dir':<20} | {'Time':<19} | {'units0':<6} | {'live_fps':<8} | {'harness_sha16':<17} | {'harness_script'}")
print("-" * 105)

for td in sorted(trips.keys(), key=lambda x: trips[x]["dt_str"] or ""):
    t = trips[td]
    mfps = f"{t['mean_live_fps']:.2f}" if t['mean_live_fps'] is not None else "None"
    u0 = str(t['units0']) if t['units0'] is not None else "None"
    hsha = str(t['harness_sha16']) if t['harness_sha16'] else "None"
    hscr = os.path.basename(t['harness_script']) if t['harness_script'] else "None"
    print(f"{td:<20} | {t['dt_str'] or 'None':<19} | {u0:<6} | {mfps:<8} | {hsha:<17} | {hscr}")
