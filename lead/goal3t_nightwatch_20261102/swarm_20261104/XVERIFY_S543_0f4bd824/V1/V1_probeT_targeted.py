"""V1 probe T: two targeted questions.

(1) Resolve the document's §四 score-table numbers for l3_20261023r by printing the exact
    5x9 bitmaps of the 损失数 column (3 digit cells, pitch 6, right edge 369) for rows 1-2,
    and the 分数 / 建造数 columns, with an ink mask that excludes the row separator lines.

(2) Identify the 4 byte-identical 'no-panel' shots: compare them with a score screen of the
    SAME trip (archive_T33 w1 vs w2) outside the score panel, to see whether the background
    artwork is the same image (=> the score table is drawn over the briefing artwork, and the
    no-panel shot is that artwork without the table).
"""
import os
import numpy as np
from PIL import Image

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
V1 = "D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/V1"


def digits(path, ytop, xright, n=3, tag=""):
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    print("  --- %s y=%d xright=%d n=%d ---" % (tag, ytop, xright, n))
    for i in range(n):
        xr = xright - 6 * (n - 1 - i)
        xl = xr - 4
        w = a[ytop:ytop + 9, xl - 1:xr + 2]      # 7 cols wide window, digit is 5
        mx = w.max(axis=2)
        # ink = clearly brighter than the darkest 1/3 of the window (text is light)
        thr = np.percentile(mx, 45) + 35
        m = mx > thr
        print("    digit @cols %d-%d:" % (xl, xr))
        for r in range(9):
            print("       " + "".join("#" if m[r, c] else "." for c in range(7)))


p = ROOT + "/l3_20261023r/measure_w2_end_x.png"
print("=== (1) l3_20261023r score table, column right edges 369 / 451 / 528 ===")
for ytop, rt in [(199, "row 1"), (236, "row 2")]:
    digits(p, ytop, 369, 3, rt + " 损失数(3rd col from right of 建造数)")
    digits(p, ytop, 451, 1, rt + " 建造数")
    digits(p, ytop, 528, 6, rt + " 分数")

print()
print("=== (2) is the artwork behind the score panel the same image? ===")
A = np.asarray(Image.open(ROOT + "/archive_T33/measure_w1_end_x.png").convert("RGB")).astype(int)
B = np.asarray(Image.open(ROOT + "/archive_T33/measure_w2_end_x.png").convert("RGB")).astype(int)
C = np.asarray(Image.open(ROOT + "/archive_T42/measure_w1_end_x.png").convert("RGB")).astype(int)
regions = {
    "sidebar right (x660-800,y0-110)": (0, 110, 660, 800),
    "sidebar right (x660-800,y110-600)": (110, 600, 660, 800),
    "artwork left (x0-95,y0-600)": (0, 600, 0, 95),
    "artwork mid (x95-660,y100-600) = panel area": (100, 600, 95, 660),
    "artwork top strip (x95-660,y0-100)": (0, 100, 95, 660),
}
for name, (y0, y1, x0, x1) in regions.items():
    da = np.abs(A[y0:y1, x0:x1] - B[y0:y1, x0:x1]).max(axis=2)
    dc = np.abs(C[y0:y1, x0:x1] - B[y0:y1, x0:x1]).max(axis=2)
    print("  %-46s T33w1-vs-T33w2: same=%.3f%%  maxdiff=%3d | T42w1-vs-T33w2: same=%.3f%%" % (
        name, 100.0 * (da == 0).mean(), da.max(), 100.0 * (dc == 0).mean()))

print()
print("=== (3) l1_20261023e4/w2 : what screen? colour histogram top colours ===")
D = np.asarray(Image.open(ROOT + "/l1_20261023e4/measure_w2_end_x.png").convert("RGB"))
flat = D.reshape(-1, 3)
vals, cnt = np.unique(flat, axis=0, return_counts=True)
o = np.argsort(-cnt)[:12]
for i in o:
    print("    colour %-14s x%d (%.2f%%)" % (tuple(vals[i]), cnt[i], 100.0 * cnt[i] / flat.shape[0]))
Image.fromarray(D).save(V1 + "/V1_probeT_l1_20261023e4_w2.png")
