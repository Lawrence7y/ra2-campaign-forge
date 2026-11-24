"""V1 probe M: read the score TABLE numeric cells straight from pixels (ASCII bitmaps).
Row 1 ink rows ~196-209, row 2 ~235-246 (measured from the w1/w2 diff bands in probe K).
Text colour in the table is light (cyan for the human row, red for the AI row), so the
mask is 'bright vs the semi-transparent dark panel', not HUD-yellow.
Prints per-cell ASCII bitmaps so the digits are read off the printed shapes."""
import os
import numpy as np
from PIL import Image

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"


def run(img_path, rows, cols, thresh):
    a = np.asarray(Image.open(img_path).convert("RGB")).astype(int)
    sub = a[rows[0]:rows[1], cols[0]:cols[1]]
    # "bright" = max channel above thresh AND not deep-blue panel background
    mx = sub.max(axis=2)
    m = mx > thresh
    cs = m.sum(axis=0)
    x = 0
    cells = []
    while x < m.shape[1]:
        if cs[x] > 0:
            y = x
            while y < m.shape[1] and cs[y] > 0:
                y += 1
            blk = m[:, x:y]
            ys, xs = np.where(blk)
            bb = blk[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            cells.append((cols[0] + x, cols[0] + y - 1, bb))
            x = y
        else:
            x += 1
    return cells


for tag, rel, rows in [("l3/w2", "l3_20261023r/measure_w2_end_x.png", (192, 214)),
                       ("l3/w2 row2", "l3_20261023r/measure_w2_end_x.png", (231, 253)),
                       ("T33/w1", "archive_T33/measure_w1_end_x.png", (192, 214)),
                       ("T33/w1 row2", "archive_T33/measure_w1_end_x.png", (231, 253)),
                       ("T34/w1", "archive_T34/measure_w1_end_x.png", (192, 214)),
                       ("T34/w1 row2", "archive_T34/measure_w1_end_x.png", (231, 253)),
                       ("T40/w1", "archive_T40/measure_w1_end_x.png", (192, 214)),
                       ("T44/w1", "archive_T44/measure_w1_end_x.png", (192, 214)),
                       ("T49/w1", "archive_T49_u0800/measure_w1_end_x.png", (192, 214))]:
    print("=" * 80)
    print(tag, rel, "ink rows", rows)
    cells = run(ROOT + "/" + rel, rows, (95, 540), 150)
    print("cells=%d  spans=%s" % (len(cells), [(c[0], c[1]) for c in cells]))
    for i, (x0, x1, bb) in enumerate(cells):
        print("  cell %2d cols %3d-%3d bbox %dx%d" % (i, x0, x1, bb.shape[1], bb.shape[0]))
        for r in range(bb.shape[0]):
            print("       " + "".join("#" if v else "." for v in bb[r]))
