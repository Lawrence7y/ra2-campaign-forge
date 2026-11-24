import os
from PIL import Image
import numpy as np

BASE_DIR = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUT_DIR = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\XVERIFY_S543_0a451d0b\V1"

pairs = [
    "archive_T34",
    "archive_T36",
    "archive_T40",
    "archive_T41",
    "archive_T43",
    "archive_T44",
    "archive_T49_u0800",
]

print("=== Analyzing full image differences between w1 and w2 ===")
for trip in pairs:
    p1 = os.path.join(BASE_DIR, trip, "measure_w1_end_x.png")
    p2 = os.path.join(BASE_DIR, trip, "measure_w2_end_x.png")
    im1 = np.array(Image.open(p1).convert("RGB"))
    im2 = np.array(Image.open(p2).convert("RGB"))
    
    diff = np.abs(im1.astype(int) - im2.astype(int))
    diff_mask = np.any(diff > 0, axis=-1)
    diff_count = np.count_nonzero(diff_mask)
    max_diff = np.max(diff)
    
    # Where are the differences located?
    y_idxs, x_idxs = np.where(diff_mask)
    if len(y_idxs) > 0:
        ymin, ymax = y_idxs.min(), y_idxs.max()
        xmin, xmax = x_idxs.min(), x_idxs.max()
        print(f"{trip:20s}: diff_px={diff_count:6d} / {im1.shape[0]*im1.shape[1]} ({diff_count/(im1.shape[0]*im1.shape[1])*100:.2f}%) | max_diff={max_diff:3d} | bbox=[y:{ymin}..{ymax}, x:{xmin}..{xmax}]")
    else:
        print(f"{trip:20s}: PERFECT ZERO DIFF (entire image identical)")
