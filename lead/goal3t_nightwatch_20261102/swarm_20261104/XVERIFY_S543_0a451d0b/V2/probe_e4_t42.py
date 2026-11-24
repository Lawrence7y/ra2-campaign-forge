# -*- coding: utf-8 -*-
import glob
import json
import os

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# 1. Investigate l1_20261023e4
print("=================== l1_20261023e4 ===================")
e4_dir = os.path.join(BASE, "l1_20261023e4")
for jf in ["_launch_result.json", "MANIFEST.json", "except_set_diff.json", "qc151_run_log.json"]:
    p = os.path.join(e4_dir, jf)
    if os.path.exists(p):
        print(f"--- {jf} ---")
        try:
            data = read_json(p)
            print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
        except Exception as e:
            print(f"Error: {e}")

# Check except_post file
for f in os.listdir(e4_dir):
    if f.startswith("except_post"):
        print(f"--- {f} ---")
        with open(os.path.join(e4_dir, f), "r", encoding="latin1") as fp:
            print(fp.read()[:1000])

# Inspect measure_w1 of e4
w1_path = os.path.join(e4_dir, "measure_w1.json")
w1_data = read_json(w1_path)
print("--- l1_20261023e4 measure_w1.json details ---")
print("error:", w1_data.get("error"))
print("verdict:", w1_data.get("verdict"))
print("n_edges:", len(w1_data.get("frame_edges", [])))
print("counters count:", len(w1_data.get("counters", [])))
if w1_data.get("counters"):
    print("counters[0]:", w1_data["counters"][0])
    print("counters[-1]:", w1_data["counters"][-1])
print("samples count:", len(w1_data.get("samples", {}).get("t", [])))
print("samples f[:10]:", w1_data.get("samples", {}).get("f", [])[:10])
print("samples f[-10:]:", w1_data.get("samples", {}).get("f", [])[-10:])
# When does f drop to 0?
f_list = w1_data.get("samples", {}).get("f", [])
t_list = w1_data.get("samples", {}).get("t", [])
for i in range(1, len(f_list)):
    if f_list[i] < f_list[i-1]:
        print(f"Drop occurred at index {i}: f went from {f_list[i-1]} (t={t_list[i-1]}) to {f_list[i]} (t={t_list[i]})")
        break

# Inspect measure_w2 of e4
w2_path = os.path.join(e4_dir, "measure_w2.json")
w2_data = read_json(w2_path)
print("--- l1_20261023e4 measure_w2.json details ---")
print("error:", w2_data.get("error"))
print("verdict:", w2_data.get("verdict"))
print("samples count:", len(w2_data.get("samples", {}).get("t", [])))
print("samples f unique:", set(w2_data.get("samples", {}).get("f", [])))
print("counters len:", len(w2_data.get("counters", [])))
if w2_data.get("counters"):
    print("counters[0]:", w2_data["counters"][0])
    print("counters[-1]:", w2_data["counters"][-1])

# 2. Investigate archive_T42
print("\n=================== archive_T42 ===================")
t42_dir = os.path.join(BASE, "archive_T42")
log_path = os.path.join(t42_dir, "T42_console.log")
if os.path.exists(log_path):
    print("--- T42_console.log (first 500 bytes and last 1000 bytes) ---")
    with open(log_path, "r", encoding="utf-8", errors="ignore") as fp:
        content = fp.read()
        print(content[:500])
        print("...")
        print(content[-1000:])

for w in [0, 1, 2]:
    p = os.path.join(t42_dir, f"measure_w{w}.json")
    if os.path.exists(p):
        d = read_json(p)
        print(f"--- T42 measure_w{w}.json ---")
        print(f"window={d.get('window')}, span_s={d.get('span_s')}, f0={d.get('frame_edges', [[None]])[0][0]}, f1={d.get('frame_edges', [[None]])[-1][0]}")
        print(f"stats: {d.get('stats')}")
        print(f"error: {d.get('error')}, verdict: {d.get('verdict')}")
        cnts = d.get("counters", [])
        print(f"counters len={len(cnts)}")
        if cnts:
            print("  cnts[0]:", cnts[0])
            print("  cnts[-1]:", cnts[-1])
