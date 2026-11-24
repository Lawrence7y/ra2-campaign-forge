"""V1 probe H: definitive pixel reader for the score-screen 时间 field.

Method (no OCR, no vision model):
  1. HUD-yellow mask.
  2. rows 120..142, cols 480..545 -> column runs (gap = empty column) = glyph cells.
  3. Normalise each cell to its own ink bounding box (10x8 padded) and hash.
  4. Print every distinct cell shape as ASCII once, with a shape id.
Shapes are then labelled by reading the printed bitmap; labels applied mechanically later.
"""
import os, glob
import numpy as np
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
files = sorted(glob.glob(os.path.join(ROOT, "*", "measure_w*_end_x.png")))

R0, R1 = 120, 142
C0, C1 = 480, 545


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
            block = sub[:, x:y]
            ys, xs = np.where(block)
            bb = block[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            out.append((C0 + x, C0 + y - 1, bb))
            x = y
        else:
            x += 1
    return out


def sig_of(bb):
    h, w = bb.shape
    canvas = np.zeros((8, 10), dtype=bool)
    canvas[:min(h, 8), :min(w, 10)] = bb[:min(h, 8), :min(w, 10)]
    return "".join("1" if v else "0" for v in canvas.ravel()), h, w


shapes = {}
lines = []
for f in files:
    rel = f[len(ROOT) + 1:].replace("\\", "/")
    a = np.asarray(Image.open(f).convert("RGB"))
    m = yellow(a)
    plate = int(m[5:30, 665:760].sum())
    cl = cells(m)
    sigs = []
    for x0, x1, bb in cl:
        s, h, w = sig_of(bb)
        shapes.setdefault(s, (h, w, bb))
        sigs.append(s)
    lines.append((rel, plate, [c[0] for c in cl], [c[1] for c in cl], sigs))
    print("%-45s plate=%3d ncell=%2d spans=%s" % (
        rel, plate, len(cl), [(c[0], c[1]) for c in cl]))

print()
print("### %d distinct cell shapes ###" % len(shapes))
order = sorted(shapes.items(), key=lambda kv: (-kv[0].count("1"), kv[1][0]))
for i, (s, (h, w, bb)) in enumerate(order):
    cnt = sum(1 for ln in lines for x in ln[4] if x == s)
    print("--- shape %02d bbox=%dx%d occurrences=%d" % (i, w, h, cnt))
    for row in range(h):
        print("      " + "".join("#" if bb[row, c] else "." for c in range(w)))
