# -*- coding: utf-8 -*-
import glob
import json
import os

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

# 1. Loading frozen window (df==0, f0==0)
print("=== Loading frozen windows (df==0, f0==0) ===")
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json"))):
    with open(p, "r", encoding="utf-8") as f:
        j = json.load(f)
    ed = j.get("frame_edges") or []
    if not ed:
        continue
    f0, f1 = ed[0][0], ed[-1][0]
    if f0 == 0 and f1 == 0:
        trip = os.path.basename(os.path.dirname(p))
        w = j.get("window")
        print(f"  {trip} w{w}: f0={f0}, f1={f1}, df={f1-f0}, span={j.get('span_s')}, stats={j.get('stats')}")

# 2. Rollback windows (df < 0)
print("\n=== Rollback windows (df < 0) ===")
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json"))):
    with open(p, "r", encoding="utf-8") as f:
        j = json.load(f)
    ed = j.get("frame_edges") or []
    if not ed:
        continue
    f0, f1 = ed[0][0], ed[-1][0]
    if f1 < f0:
        trip = os.path.basename(os.path.dirname(p))
        w = j.get("window")
        print(f"  {trip} w{w}: f0={f0}, f1={f1}, df={f1-f0}, span={j.get('span_s')}")
        print(f"    first 5 edges: {ed[:5]}")
        print(f"    last 5 edges: {ed[-5:]}")
        print(f"    stats: {j.get('stats')}")

# 3. All windows of l1_20261023e4
print("\n=== All windows of l1_20261023e4 ===")
trip_e4_dir = os.path.join(BASE, "l1_20261023e4")
if os.path.exists(trip_e4_dir):
    for fname in sorted(os.listdir(trip_e4_dir)):
        fpath = os.path.join(trip_e4_dir, fname)
        if fname.endswith(".json"):
            print(f"  File: {fname}")
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    jdata = json.load(f)
                if "frame_edges" in jdata:
                    ed = jdata["frame_edges"]
                    f0 = ed[0][0] if ed else None
                    f1 = ed[-1][0] if ed else None
                    print(f"    window={jdata.get('window')}, f0={f0}, f1={f1}, df={(f1-f0) if ed else None}, fps_avg={(jdata.get('stats') or {}).get('fps_avg')}")
                else:
                    print(f"    keys: {list(jdata.keys())}")
                    if "exit_code" in jdata or "returncode" in jdata or "error" in jdata:
                        print(f"    exit info: exit_code={jdata.get('exit_code')}, error={jdata.get('error')}")
            except Exception as e:
                print(f"    read error: {e}")
        elif not fname.endswith(".png"):
            print(f"  Other file: {fname}")

# 4. All windows and files of archive_T42
print("\n=== All windows of archive_T42 ===")
trip_t42_dir = os.path.join(BASE, "archive_T42")
if os.path.exists(trip_t42_dir):
    for fname in sorted(os.listdir(trip_t42_dir)):
        fpath = os.path.join(trip_t42_dir, fname)
        if fname.endswith(".json"):
            print(f"  File: {fname}")
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    jdata = json.load(f)
                if "frame_edges" in jdata:
                    ed = jdata["frame_edges"]
                    f0 = ed[0][0] if ed else None
                    f1 = ed[-1][0] if ed else None
                    print(f"    window={jdata.get('window')}, f0={f0}, f1={f1}, df={(f1-f0) if ed else None}, fps_avg={(jdata.get('stats') or {}).get('fps_avg')}")
                else:
                    print(f"    keys: {list(jdata.keys())}")
            except Exception as e:
                print(f"    read error: {e}")
        elif not fname.endswith(".png"):
            print(f"  Other file: {fname}")
