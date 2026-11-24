import os
import glob
import json

TRIPS = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

all_files = glob.glob(os.path.join(TRIPS, "measure_w*.json")) + glob.glob(os.path.join(TRIPS, "*", "measure_w*.json"))

trip_all_wins = {}
for f in all_files:
    trip_dir = os.path.dirname(f)
    tname = os.path.basename(trip_dir) if trip_dir != TRIPS else "_ROOT_"
    wname = os.path.basename(f)
    with open(f, "r", encoding="utf-8") as fp:
        d = json.load(fp)
    pre = d.get("gate", {}).get("pre_fps15")
    trip_all_wins.setdefault(tname, []).append((wname, pre))

multi_all = {k: v for k, v in trip_all_wins.items() if len(v) > 1}
print(f"Total trips with >1 window (all 103 files): {len(multi_all)}")
dup_all = 0
for tname, wins in multi_all.items():
    pres = set(p for w, p in wins)
    if len(pres) == 1:
        dup_all += 1
    else:
        print(f"Diff pre: {tname}: {wins}")
print(f"Identical pre_fps15: {dup_all}/{len(multi_all)}")
