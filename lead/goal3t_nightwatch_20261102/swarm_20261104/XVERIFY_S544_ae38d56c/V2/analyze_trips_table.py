# -*- coding: utf-8 -*-
"""Analyze harness versions, maps, args, and performance across all trips."""
import glob
import hashlib
import json
import os

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

def file_sha16(p):
    if os.path.exists(p):
        return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
    return "NOT_FOUND"

for td, tinfo in trips.items():
    pdir = os.path.join(TRIP_BASE, td) if td != "." else TRIP_BASE
    
    # Check _launch_result.json
    lr_path = os.path.join(pdir, "_launch_result.json")
    lr_data = {}
    if os.path.exists(lr_path):
        try:
            with open(lr_path, "r", encoding="utf-8") as f:
                lr_data = json.load(f)
        except Exception:
            pass

    harness_path = lr_data.get("harness")
    harness_sha16 = lr_data.get("harness_sha16")
    argv = lr_data.get("argv") or []
    if argv and not harness_path:
        harness_path = argv[0]

    # Target map
    target_map = None
    target_sha256 = None
    h8_wait_frame = None
    for i, a in enumerate(argv):
        if a == "--target-map" and i + 1 < len(argv):
            target_map = argv[i + 1]
        elif a == "--target-sha256" and i + 1 < len(argv):
            target_sha256 = argv[i + 1]
        elif a == "--h8-wait-frame" and i + 1 < len(argv):
            h8_wait_frame = argv[i + 1]

    # If harness_sha16 not found, compute from harness_path if exists
    if not harness_sha16 and harness_path:
        harness_sha16 = file_sha16(harness_path)

    # If target_sha256 not found, check map_sha256 from measure
    if not target_sha256:
        target_sha256 = tinfo["map_sha256"]

    # Compute live_fps for each window
    live_fps_list = [w["live_fps"] for w in tinfo["windows"] if w["live_fps"] is not None and w["live_fps"] > 0]
    mean_live_fps = sum(live_fps_list) / len(live_fps_list) if live_fps_list else None

    tinfo["harness_path"] = harness_path
    tinfo["harness_sha16"] = harness_sha16
    tinfo["harness_name"] = os.path.basename(harness_path) if harness_path else "unknown"
    tinfo["target_map"] = os.path.basename(target_map) if target_map else "unknown"
    tinfo["target_sha256_8"] = target_sha256[:12] if target_sha256 else "unknown"
    tinfo["h8_wait_frame"] = h8_wait_frame
    tinfo["mean_live_fps"] = mean_live_fps
    tinfo["live_fps_wins"] = [round(w["live_fps"], 2) if w["live_fps"] is not None else None for w in tinfo["windows"]]
    tinfo["pre_fps15_wins"] = [round(w["pre_fps15"], 2) if w["pre_fps15"] is not None else None for w in tinfo["windows"]]

print("=== ALL TRIPS DETAILED TABLE ===")
header = f"{'Trip Dir':<18} | {'Date/Time':<19} | {'u0':<5} | {'live_fps wins':<22} | {'mean':<6} | {'harness':<24} | {'h_sha16':<17} | {'map_sha':<12} | {'h8_frame'}"
print(header)
print("-" * len(header))

for td in sorted(trips.keys(), key=lambda x: trips[x]["dt_str"] or ""):
    t = trips[td]
    dt = t["dt_str"] or "unknown"
    u0 = str(t["units0"]) if t["units0"] is not None else "None"
    fps_w = str(t["live_fps_wins"])
    mfps = f"{t['mean_live_fps']:.2f}" if t["mean_live_fps"] is not None else "None"
    hname = t["harness_name"]
    hsha = t["harness_sha16"] or "None"
    msha = t["target_sha256_8"]
    h8f = str(t["h8_wait_frame"])
    print(f"{td:<18} | {dt:<19} | {u0:<5} | {fps_w:<22} | {mfps:<6} | {hname:<24} | {hsha:<17} | {msha:<12} | {h8f}")
