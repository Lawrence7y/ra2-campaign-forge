"""Read-only probe #2 (my own, independent of V1's scripts):
ASCII bitmap of the yellow 'time' field + run segmentation, for chosen screenshots.
Band rows came from my own row-profile in V1RC_explore_yellow.py (rows 124..138), widened."""
import os
import numpy as np
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

TARGETS = [
    "archive_T38/measure_w2_end_x.png", "archive_T38/measure_w1_end_x.png",
    "measure_w1_end_x.png", "measure_w2_end_x.png",
    "l3_20261023r/measure_w2_end_x.png",
    "archive_T34/measure_w1_end_x.png", "archive_T34/measure_w2_end_x.png",
    "archive_T33/measure_w1_end_x.png", "archive_T44/measure_w1_end_x.png",
    "archive_T44/measure_w2_end_x.png", "archive_T43/measure_w1_end_x.png",
    "archive_T49_u0800/measure_w1_end_x.png", "archive_T36/measure_w2_end_x.png",
    "archive_T45/measure_w1_end_x.png", "archive_T41/measure_w1_end_x.png",
    "archive_T40/measure_w1_end_x.png", "archive_T39/measure_w2_end_x.png",
    "archive_T36/measure_w1_end_x.png", "archive_T42/measure_w1_end_x.png",
]
R0, R1 = 118, 145
CUT = 430          # digits live right of the CJK label
for rel in TARGETS:
    a = np.asarray(Image.open(os.path.join(ROOT, rel.replace("/", os.sep))).convert("RGB"), dtype=np.int16)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    m = (R > 200) & (G > 200) & (B < 110)
    band = m[R0:R1 + 1]
    cols = np.where(band.any(0))[0]
    if len(cols) == 0:
        print(f"=== {rel}: NO YELLOW in rows {R0}-{R1}")
        continue
    anyc = band.any(0)
    runs, x = [], 0
    while x < len(anyc):
        if anyc[x]:
            y = x
            while y + 1 < len(anyc) and anyc[y + 1]:
                y += 1
            runs.append((x, y, int(band[:, x:y + 1].sum())))
            x = y + 1
        else:
            x += 1
    print(f"=== {rel}  yellow_cols({cols.min()}..{cols.max()}) n_runs={len(runs)}")
    print("    runs(col0,col1,npix):", runs)
    sub = band[:, CUT:]
    for r in range(sub.shape[0]):
        print(f"    {R0+r:3d} " + "".join("#" if v else "." for v in sub[r]))
