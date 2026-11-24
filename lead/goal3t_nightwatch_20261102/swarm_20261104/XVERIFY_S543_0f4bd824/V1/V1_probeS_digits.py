"""V1 probe S: print the numeric columns of the two score-table rows as ASCII bitmaps,
using a LOCAL-BACKGROUND-relative ink mask (background = median colour of the row band).

Numeric column windows were measured from probe N/K: the four right-aligned digit columns
end at cols ~286, ~369, ~451, ~528 (each digit 5 px wide, 1 px gap, 9 px tall).
"""
import os
import numpy as np
from PIL import Image

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

RANGES = [(250, 292, "c1"), (330, 375, "c2"), (415, 457, "c3"), (470, 534, "c4")]
ROWS = [(194, 212, "row1"), (232, 250, "row2")]

TARGETS = ["l3_20261023r/measure_w2_end_x.png",
           "archive_T33/measure_w1_end_x.png",
           "archive_T40/measure_w1_end_x.png",
           "archive_T41/measure_w1_end_x.png",
           "archive_T44/measure_w1_end_x.png",
           "archive_T49_u0800/measure_w1_end_x.png",
           "archive_T34/measure_w1_end_x.png"]

for rel in TARGETS:
    a = np.asarray(Image.open(ROOT + "/" + rel).convert("RGB")).astype(int)
    print("=" * 78)
    print(rel)
    for (y0, y1, rtag) in ROWS:
        band = a[y0:y1, 95:545]
        bg = np.median(band.reshape(-1, 3), axis=0)
        d = np.abs(band - bg).max(axis=2)
        m = d > 60
        print("  %s  bg=%s  ink px=%d" % (rtag, bg.astype(int), int(m.sum())))
        for (x0, x1, ctag) in RANGES:
            sub = m[y0 - y0:y1 - y0, x0 - 95:x1 - 95]
            cols = sub.sum(axis=0)
            runs = []
            x = 0
            while x < sub.shape[1]:
                if cols[x] > 0:
                    y = x
                    while y < sub.shape[1] and cols[y] > 0:
                        y += 1
                    runs.append((x0 + x, x0 + y - 1))
                    x = y
                else:
                    x += 1
            print("    %s cols %d-%d runs=%s" % (ctag, x0, x1, runs))
            for r in range(sub.shape[0]):
                line = "".join("#" if sub[r, c] else "." for c in range(sub.shape[1]))
                if line.strip("."):
                    print("      %3d|%s" % (y0 + r, line))
