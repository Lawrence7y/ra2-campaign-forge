import os
from PIL import Image
import numpy as np

BASE_DIR = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

pairs = [
    "archive_T34",
    "archive_T36",
    "archive_T40",
    "archive_T41",
    "archive_T43",
    "archive_T44",
    "archive_T49_u0800",
]

# Panels and text boxes
# TITLE: (620, 10, 790, 45)
# TIMER: (430, 115, 620, 150)
# SCORE_TABLE: (80, 100, 640, 280)

print(f"{'Trip':20s} | {'Title MaxDiff':13s} | {'Timer MaxDiff':13s} | {'Table MaxDiff':13s} | {'Full MaxDiff':12s}")
print("-" * 80)
for trip in pairs:
    p1 = os.path.join(BASE_DIR, trip, "measure_w1_end_x.png")
    p2 = os.path.join(BASE_DIR, trip, "measure_w2_end_x.png")
    im1 = np.array(Image.open(p1).convert("RGB"))
    im2 = np.array(Image.open(p2).convert("RGB"))
    
    title_diff = np.max(np.abs(im1[10:45, 620:790].astype(int) - im2[10:45, 620:790].astype(int)))
    timer_diff = np.max(np.abs(im1[115:150, 430:620].astype(int) - im2[115:150, 430:620].astype(int)))
    table_diff = np.max(np.abs(im1[100:280, 80:640].astype(int) - im2[100:280, 80:640].astype(int)))
    full_diff = np.max(np.abs(im1.astype(int) - im2.astype(int)))
    
    print(f"{trip:20s} | {title_diff:13d} | {timer_diff:13d} | {table_diff:13d} | {full_diff:12d}")
