import os
import glob
import json

TRIPS = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

root_files = glob.glob(os.path.join(TRIPS, "measure_w*.json"))
sub_files = glob.glob(os.path.join(TRIPS, "*", "measure_w*.json"))

print(f"Root files count: {len(root_files)}")
for f in root_files:
    print("  Root file:", os.path.basename(f))

print(f"Sub files count: {len(sub_files)}")
sub_dirs = set(os.path.dirname(f) for f in sub_files)
print(f"Sub dirs count: {len(sub_dirs)}")
print(f"Total measure_w*.json count: {len(root_files) + len(sub_files)}")
