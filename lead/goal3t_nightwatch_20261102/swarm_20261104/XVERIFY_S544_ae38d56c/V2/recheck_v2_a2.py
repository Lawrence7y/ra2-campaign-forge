import os
import glob
import json
import math

TRIPS = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

# First, find harness version for each trip
trip_harness = {}
trip_dirs = glob.glob(os.path.join(TRIPS, "*"))
for td in trip_dirs:
    if not os.path.isdir(td):
        continue
    tname = os.path.basename(td)
    # Check _launch_result.json
    lr_path = os.path.join(td, "_launch_result.json")
    qf_path = os.path.join(td, "qc151_fields.json")
    
    harness_script = None
    harness_sha16 = None
    start_frame = None
    
    if os.path.exists(lr_path):
        with open(lr_path, "r", encoding="utf-8", errors="ignore") as fp:
            try:
                lr = json.load(fp)
                cmd = lr.get("command") or lr.get("cmd") or lr.get("argv")
                harness_sha16 = lr.get("harness_sha16") or lr.get("script_sha16")
                if isinstance(cmd, list):
                    for item in cmd:
                        if "harness" in item:
                            harness_script = item
                elif isinstance(cmd, str):
                    for item in cmd.split():
                        if "harness" in item:
                            harness_script = item
            except Exception as e:
                pass

    if os.path.exists(qf_path):
        with open(qf_path, "r", encoding="utf-8", errors="ignore") as fp:
            try:
                qf = json.load(fp)
                if not harness_script:
                    harness_script = qf.get("harness_script") or qf.get("script")
                if not harness_sha16:
                    harness_sha16 = qf.get("harness_sha16")
                start_frame = qf.get("h7_measure_start_frame") or qf.get("h8_measure_start_frame") or qf.get("measure_start_frame")
            except Exception as e:
                pass
                
    trip_harness[tname] = {
        "harness_script": harness_script,
        "harness_sha16": harness_sha16,
        "start_frame": start_frame,
    }

# Also root files trip
trip_harness["_ROOT_"] = {"harness_script": None, "harness_sha16": None, "start_frame": None}

all_files = glob.glob(os.path.join(TRIPS, "measure_w*.json")) + glob.glob(os.path.join(TRIPS, "*", "measure_w*.json"))

windows_in_range = []

for f in all_files:
    with open(f, "r", encoding="utf-8") as fp:
        d = json.load(fp)
    edges = d.get("frame_edges", [])
    if len(edges) < 2:
        continue
    f0, t0 = edges[0]
    f1, t1 = edges[-1]
    df = f1 - f0
    dt = t1 - t0
    if df <= 0 or dt <= 0:
        continue
    live_fps = df / dt
    
    u0 = d.get("gate", {}).get("units0")
    if u0 is None:
        continue
    
    trip_dir = os.path.dirname(f)
    tname = os.path.basename(trip_dir) if trip_dir != TRIPS else "_ROOT_"
    wname = os.path.basename(f)
    map_sha = d.get("map_sha256")
    
    if 1180 <= u0 <= 1360:
        hinfo = trip_harness.get(tname, {})
        windows_in_range.append({
            "trip": tname,
            "window": wname,
            "units0": u0,
            "live_fps": live_fps,
            "map_sha": map_sha,
            "harness": hinfo.get("harness_script"),
            "sha16": hinfo.get("harness_sha16"),
            "start_frame": hinfo.get("start_frame")
        })

print(f"Total valid windows in [1180, 1360]: {len(windows_in_range)}")
fast = []
slow = []
mid = []

for w in sorted(windows_in_range, key=lambda x: (x["trip"], x["window"])):
    fps = w["live_fps"]
    cat = "FAST" if fps >= 28 else ("SLOW" if fps < 15 else "MID")
    if cat == "FAST": fast.append(w)
    elif cat == "SLOW": slow.append(w)
    else: mid.append(w)
    print(f"[{cat:4s}] {w['trip']}/{w['window']}: units0={w['units0']}, live_fps={fps:.4f}, harness={w['harness']}, sha16={w['sha16']}, start_frame={w['start_frame']}")

print(f"\nSummary in [1180, 1360]:")
print(f"Fast (>= 28 fps): {len(fast)}")
print(f"Slow (< 15 fps): {len(slow)}")
print(f"Mid (15 <= fps < 28): {len(mid)}")

# Check v4 vs non-v4
# A window is v4 if 'v4' is in harness or sha16 == '38244d2907e7f7fa'
def is_v4(w):
    h = str(w['harness']) + " " + str(w['sha16']) + " " + str(w['trip'])
    return "v4" in h or "38244d2907e7f7fa" in h

fast_v4 = sum(1 for w in fast if is_v4(w))
fast_nonv4 = sum(1 for w in fast if not is_v4(w))
slow_v4 = sum(1 for w in slow if is_v4(w))
slow_nonv4 = sum(1 for w in slow if not is_v4(w))

print(f"\n2x2 table (fast/slow x v4/non-v4):")
print(f"          v4    non-v4")
print(f"fast      {fast_v4:<5} {fast_nonv4:<5}")
print(f"slow      {slow_v4:<5} {slow_nonv4:<5}")

ad_bc = fast_v4 * slow_nonv4 - fast_nonv4 * slow_v4
denom = math.sqrt((fast_v4 + fast_nonv4) * (slow_v4 + slow_nonv4) * (fast_v4 + slow_v4) * (fast_nonv4 + slow_nonv4))
phi = ad_bc / denom if denom > 0 else 0
print(f"phi coefficient = {phi:.6f}")
