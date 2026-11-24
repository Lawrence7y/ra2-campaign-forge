"""V1 probe E: glyph-cell decomposition of the 时间 value field.

Steps, all from pixels:
 1. HUD-yellow mask.
 2. Restrict to the header band rows 120-140, cols 380-560.
 3. Column projection -> split into glyph cells by empty columns.
 4. Print each cell as a labelled ASCII bitmap (row indices absolute).
Cells are then clustered by identical bitmap across images, so a digit is identified
once from one image and propagated mechanically.
"""
import os, glob, json
import numpy as np
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
files = sorted(glob.glob(os.path.join(ROOT, "*", "measure_w*_end_x.png")))

R0, R1 = 120, 141
C0, C1 = 380, 560


def yellow(a):
    r = a[:, :, 0].astype(int); g = a[:, :, 1].astype(int); b = a[:, :, 2].astype(int)
    return (r > 170) & (g > 150) & (b < 130) & ((r - b) > 70) & ((g - b) > 50)


def cells(m):
    sub = m[R0:R1, C0:C1]
    colsum = sub.sum(axis=0)
    out = []
    x = 0
    while x < sub.shape[1]:
        if colsum[x] > 0:
            y = x
            while y < sub.shape[1] and colsum[y] > 0:
                y += 1
            out.append((C0 + x, C0 + y - 1))
            x = y
        else:
            x += 1
    return sub, out


for f in files:
    rel = f[len(ROOT) + 1:].replace("\\", "/")
    a = np.asarray(Image.open(f).convert("RGB"))
    m = yellow(a)
    tp = int(m[5:30, 665:760].sum())
    sub, cl = cells(m)
    print("=" * 78)
    print("%-45s title-plate=%d  cells=%d" % (rel, tp, len(cl)))
    for i, (x0, x1) in enumerate(cl):
        print("  cell %2d cols %3d-%3d w=%2d" % (i, x0, x1, x1 - x0 + 1))
        for y in range(sub.shape[0]):
            print("     %3d| %s" % (R0 + y, "".join("#" if sub[y, x - C0] else "." for x in range(x0, x1 + 1))))
