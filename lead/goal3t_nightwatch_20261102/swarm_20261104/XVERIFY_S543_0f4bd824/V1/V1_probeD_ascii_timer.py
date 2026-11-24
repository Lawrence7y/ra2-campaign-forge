"""V1 probe D: render the score-screen header strip as ASCII art of the 'HUD yellow' mask,
so the digits of 时间 HH:MM:SS can be read directly from text output (independent of any
vision model / OCR). Also reports objective presence markers.
Read-only on data.
"""
import os, glob
import numpy as np
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
files = sorted(glob.glob(os.path.join(ROOT, "*", "measure_w*_end_x.png")))


def yellow(a):
    r = a[:, :, 0].astype(int); g = a[:, :, 1].astype(int); b = a[:, :, 2].astype(int)
    return (r > 170) & (g > 150) & (b < 130) & ((r - b) > 70) & ((g - b) > 50)


for f in files:
    rel = f[len(ROOT) + 1:].replace("\\", "/")
    a = np.asarray(Image.open(f).convert("RGB"))
    m = yellow(a)
    print("=" * 78)
    print(rel)
    # marker 1: title plate region top-right of the metal panel
    t = m[5:30, 665:760]
    print("  title-plate(665-760,5-30) yellow px = %d" % t.sum())
    # marker 2/3: header row band and column-header band inside the table
    h1 = m[120:142, 90:560]
    h2 = m[156:178, 90:560]
    print("  hdr-row  (90-560,120-142) yellow px = %d" % h1.sum())
    print("  col-hdr  (90-560,156-178) yellow px = %d" % h2.sum())
    # ASCII render of the right-hand part of the header row (where 时间 lives)
    sub = m[118:144, 380:560]
    print("  --- ASCII rows118-143 cols380-559 ('#' = HUD yellow) ---")
    for y in range(sub.shape[0]):
        line = "".join("#" if sub[y, x] else "." for x in range(sub.shape[1]))
        if line.strip("."):
            print("   %3d| %s" % (118 + y, line))
