import os
import glob
import json

TRIPS = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

files = glob.glob(os.path.join(TRIPS, "measure_w*.json")) + glob.glob(os.path.join(TRIPS, "*", "measure_w*.json"))

c_ge2 = 0
c_wrap = 0
c_pos = 0
c_1 = 0
c_0 = 0
missing = 0

wrap_files = []

for f in files:
    with open(f, "r", encoding="utf-8") as fp:
        data = json.load(fp)
    edges = data.get("frame_edges")
    if edges is None:
        missing += 1
        continue
    L = len(edges)
    if L == 0:
        c_0 += 1
    elif L == 1:
        c_1 += 1
    else:
        c_ge2 += 1
        f0, t0 = edges[0]
        f1, t1 = edges[-1]
        df = f1 - f0
        dt = t1 - t0
        if df > 0 and dt > 0:
            c_pos += 1
        else:
            c_wrap += 1
            wrap_files.append((f, f0, f1, df, dt))

print(f"Total files: {len(files)}")
print(f"Missing frame_edges: {missing}")
print(f"len == 0: {c_0}")
print(f"len == 1: {c_1}")
print(f"len >= 2: {c_ge2}")
print(f"  df > 0 and dt > 0: {c_pos}")
print(f"  wrap/non-pos: {c_wrap}")
for w in wrap_files:
    print("  wrap file:", w)
