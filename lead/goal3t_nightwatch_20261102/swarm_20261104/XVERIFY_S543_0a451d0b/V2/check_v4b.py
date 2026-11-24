# -*- coding: utf-8 -*-
import glob
import json
import os

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
v4b_dir = os.path.join(BASE, "l3_1101v4b")

print("Files in l3_1101v4b:", os.listdir(v4b_dir) if os.path.exists(v4b_dir) else "NOT FOUND")

for fname in os.listdir(v4b_dir):
    if fname.endswith(".json"):
        p = os.path.join(v4b_dir, fname)
        with open(p, "r", encoding="utf-8") as f:
            j = json.load(f)
        print(f"--- {fname} ---")
        print("keys:", list(j.keys()))
        if "frame_edges" in j:
            print("frame_edges len:", len(j["frame_edges"]))
        if "stats" in j:
            print("stats:", j["stats"])
        if "samples" in j:
            print("samples keys:", list(j["samples"].keys()) if isinstance(j["samples"], dict) else len(j["samples"]))
            if isinstance(j["samples"], dict):
                print("t len:", len(j["samples"].get("t", [])))
                print("f len:", len(j["samples"].get("f", [])))
                f_arr = j["samples"].get("f", [])
                if f_arr:
                    print("f[0]:", f_arr[0], "f[-1]:", f_arr[-1])
