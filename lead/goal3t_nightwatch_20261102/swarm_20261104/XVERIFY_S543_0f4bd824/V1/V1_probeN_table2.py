"""V1 probe N: score-table content, region-targeted (no giant highlight blobs).

Prints ASCII bitmaps for:
  A) column-header band  rows 156-180 (which column means what)
  B) data row 1          rows 192-214, cols 320-540 (numeric columns only)
  C) data row 2          rows 231-253, cols 320-540
  D) data row 3          rows 270-292, cols 320-540
"""
import os, glob
import numpy as np
from PIL import Image

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"


def cells_for(img, rows, cols, thresh):
    a = np.asarray(Image.open(img).convert("RGB")).astype(int)
    sub = a[rows[0]:rows[1], cols[0]:cols[1]]
    mx = sub.max(axis=2)
    m = mx > thresh
    cs = m.sum(axis=0)
    out, x = [], 0
    while x < m.shape[1]:
        if cs[x] > 0:
            y = x
            while y < m.shape[1] and cs[y] > 0:
                y += 1
            blk = m[:, x:y]
            ys, xs = np.where(blk)
            out.append((cols[0] + x, cols[0] + y - 1, blk[ys.min():ys.max() + 1, xs.min():xs.max() + 1]))
            x = y
        else:
            x += 1
    return out


def show(tag, img, rows, cols, thresh=150, maxcells=40):
    print("-" * 76)
    print("%s  rows %s cols %s thresh=%d" % (tag, rows, cols, thresh))
    cl = cells_for(img, rows, cols, thresh)
    print("   ncells=%d spans=%s" % (len(cl), [(c[0], c[1]) for c in cl][:maxcells]))
    for i, (x0, x1, bb) in enumerate(cl[:maxcells]):
        if bb.shape[0] * bb.shape[1] > 900:
            print("   cell %2d cols %3d-%3d BIG blob %dx%d (skipped)" % (i, x0, x1, bb.shape[1], bb.shape[0]))
            continue
        print("   cell %2d cols %3d-%3d %dx%d" % (i, x0, x1, bb.shape[1], bb.shape[0]))
        for r in range(bb.shape[0]):
            print("        " + "".join("#" if v else "." for v in bb[r]))


TARGETS = ["l3_20261023r/measure_w2_end_x.png",
           "archive_T34/measure_w1_end_x.png",
           "archive_T40/measure_w1_end_x.png",
           "archive_T44/measure_w1_end_x.png",
           "archive_T49_u0800/measure_w1_end_x.png",
           "archive_T33/measure_w1_end_x.png"]

for rel in TARGETS:
    p = ROOT + "/" + rel
    print("=" * 80)
    print(rel)
    show("A column-header band", p, (156, 180), (90, 540), thresh=150)
    show("B row1 numerics", p, (192, 214), (320, 540), thresh=150)
    show("C row2 numerics", p, (231, 253), (320, 540), thresh=140)
    show("D row3 numerics", p, (270, 292), (320, 540), thresh=140)
