"""Read-only probe #3 (mine): cut the 6 digit cells of the yellow HH:MM:SS timer and print
each cell's bitmap separately so a digit can be read from its shape. Cell x-positions are
found by my own column-run segmentation of rows 118..145 (see V1RC_timer_ascii_out.txt):
the value lives right of the '时间' label, in 6 runs of width<=6 separated by 2-colon runs.
Threshold used here: R>200 & G>200 & B<110 (my own, differs from the report's)."""
import os
import numpy as np
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
R0, R1 = 118, 145

def cells(path):
    a = np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)
    m = (a[..., 0] > 200) & (a[..., 1] > 200) & (a[..., 2] < 110)
    band = m[R0:R1 + 1]
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
    # digit cells = runs of width 4..6 with >=8 px ink, in the right half
    dig = [(c0, c1) for (c0, c1, n) in runs if c0 > 400 and 4 <= c1 - c0 <= 6 and n >= 8]
    val = [(c0, c1) for (c0, c1) in dig if c1 >= 480]
    return band, runs, val

files = sorted(f for f in os.listdir(ROOT) if f.startswith("measure_w") and f.endswith("_end_x.png"))
subdirs = sorted(d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d)))
for d in subdirs:
    for f in sorted(os.listdir(os.path.join(ROOT, d))):
        if f.startswith("measure_w") and f.endswith("_end_x.png"):
            files.append(os.path.join(d, f))

for rel in files:
    band, runs, val = cells(os.path.join(ROOT, rel.replace("/", os.sep)))
    if len(val) != 6:
        print(f"### {rel}: digit cells found = {len(val)} -> {val}  (runs={runs})")
        continue
    print(f"### {rel}  cells={val}")
    for i, (c0, c1) in enumerate(val):
        sub = band[:, c0:c1 + 1]
        rr = np.where(sub.any(1))[0]
        sub = sub[rr.min():rr.max() + 1]
        print(f"  cell{i} cols{c0}-{c1} rows{R0+rr.min()}-{R0+rr.max()} h={sub.shape[0]} w={sub.shape[1]}")
        for r in range(sub.shape[0]):
            print("    " + "".join("#" if v else "." for v in sub[r]))
