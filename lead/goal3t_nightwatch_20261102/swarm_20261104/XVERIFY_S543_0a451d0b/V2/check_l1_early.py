# -*- coding: utf-8 -*-
import glob
import json
import os

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

for t in ["l1_20261023", "l1_20261023b"]:
    tdir = os.path.join(BASE, t)
    print(f"=== {t} ===")
    for fname in sorted(os.listdir(tdir)):
        if fname.endswith(".json") and "measure" in fname:
            p = os.path.join(tdir, fname)
            with open(p, "r", encoding="utf-8") as f:
                j = json.load(f)
            print(f"  {fname}: window={j.get('window')}, span={j.get('span_s')}, f0={j.get('frame_edges', [[None]])[0][0]}, f1={j.get('frame_edges', [[None]])[-1][0]}, stats={j.get('stats')}, gate={j.get('gate')}")
            if j.get("counters"):
                print("    counters[0]:", j["counters"][0])
                print("    counters[-1]:", j["counters"][-1])
        elif fname.startswith("_launch") or fname.startswith("MANIFEST") or fname.startswith("qc151"):
            p = os.path.join(tdir, fname)
            try:
                with open(p, "r", encoding="utf-8") as f:
                    j = json.load(f)
                if isinstance(j, dict):
                    print(f"  {fname}: rc/exit={j.get('rc', j.get('final_exit', j.get('final_exit_code')))}, dur={j.get('duration_s')}")
            except Exception:
                pass
