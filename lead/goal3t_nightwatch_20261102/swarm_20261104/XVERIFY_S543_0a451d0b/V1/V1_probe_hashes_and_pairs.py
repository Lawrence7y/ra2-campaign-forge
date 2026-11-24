import os
import glob
import hashlib
from PIL import Image
import numpy as np

BASE_DIR = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
png_files = sorted(glob.glob(os.path.join(BASE_DIR, "*", "measure_w*_end_x.png")))

print(f"Matched {len(png_files)} files in subdirectories.")

# 1. SHA256 of raw RGB bytes
hash_to_files = {}
file_to_hash = {}

for p in png_files:
    rel = os.path.relpath(p, BASE_DIR)
    img = Image.open(p).convert("RGB")
    raw = img.tobytes()
    sha = hashlib.sha256(raw).hexdigest()
    file_to_hash[rel] = sha
    hash_to_files.setdefault(sha, []).append(rel)

print("\n=== SHA256 (RGB raw) Summary ===")
print(f"Total files: {len(png_files)}")
print(f"Unique hashes: {len(hash_to_files)}")

for sha, files in hash_to_files.items():
    if len(files) > 1:
        print(f"\n[DUPLICATE GROUP] SHA256={sha} (count={len(files)}):")
        for f in files:
            print(f"  - {f}")
    else:
        print(f"[UNIQUE] {sha[:16]}... : {files[0]}")

# 2. Pairs w1 vs w2 per trip
# Find trips having both w1 and w2 end_x.png
trips = {}
for rel in file_to_hash:
    parts = rel.split(os.sep)
    trip = parts[0]
    fname = parts[1]
    trips.setdefault(trip, {})[fname] = os.path.join(BASE_DIR, rel)

print("\n=== Pairwise Comparison: w1 vs w2 per trip ===")
# Time region: approximately (430, 118, 640, 150) or let's inspect the timer region specifically
# In S543, Leader mentions: "区域约 (430,118)-(640,150)"
TIMER_BOX = (430, 118, 640, 150)
PANEL_BOX = (85, 108, 630, 275)

for trip, files in sorted(trips.items()):
    w1_path = files.get("measure_w1_end_x.png")
    w2_path = files.get("measure_w2_end_x.png")
    if w1_path and w2_path:
        im1 = Image.open(w1_path).convert("RGB")
        im2 = Image.open(w2_path).convert("RGB")
        arr1 = np.array(im1)
        arr2 = np.array(im2)
        
        full_max_diff = np.max(np.abs(arr1.astype(int) - arr2.astype(int)))
        
        crop1 = im1.crop(TIMER_BOX)
        crop2 = im2.crop(TIMER_BOX)
        t_arr1 = np.array(crop1)
        t_arr2 = np.array(crop2)
        timer_diff = np.abs(t_arr1.astype(int) - t_arr2.astype(int))
        timer_max_diff = np.max(timer_diff)
        timer_diff_px = np.count_nonzero(np.any(timer_diff != 0, axis=-1))
        
        print(f"Trip {trip:20s}: Timer box {TIMER_BOX} maxdiff={timer_max_diff:3d}, diff_px={timer_diff_px:5d} / {t_arr1.shape[0]*t_arr1.shape[1]} | Full img maxdiff={full_max_diff:3d}")
