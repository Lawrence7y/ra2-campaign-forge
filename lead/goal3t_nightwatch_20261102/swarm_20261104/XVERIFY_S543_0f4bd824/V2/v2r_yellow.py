"""Find the yellow-text glyph bands in a known score screen to locate the timer field exactly."""
import os, json
import numpy as np
from PIL import Image

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
im = Image.open(os.path.join(R, "archive_T33", "measure_w1_end_x.png")).convert("RGB")
a = np.asarray(im).astype(np.int16)
r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
yellow = (r > 150) & (g > 120) & (b < 110)
print("[Y1] yellow pixel count:", int(yellow.sum()))
rows = yellow.sum(axis=1)
bands = []
inb = False
for y, v in enumerate(rows):
    if v > 0 and not inb:
        inb, y0 = True, y
    elif v == 0 and inb:
        inb = False
        bands.append((y0, y - 1, int(rows[y0:y].sum())))
if inb:
    bands.append((y0, len(rows) - 1, int(rows[y0:].sum())))
print("[Y2] yellow row bands (y0,y1,count):")
for bnd in bands:
    print("   ", bnd)

# for the two bands just under y=140 (the header row), print column clusters
for (y0, y1, n) in bands:
    if y0 > 150 or n < 20:
        continue
    cols = yellow[y0:y1 + 1].sum(axis=0)
    xs = np.where(cols > 0)[0]
    clusters = []
    start = xs[0]
    prev = xs[0]
    for x in xs[1:]:
        if x - prev > 3:
            clusters.append((int(start), int(prev)))
            start = x
        prev = x
    clusters.append((int(start), int(prev)))
    print(f"    band y={y0}-{y1}: column clusters {clusters}")
    # glyph-level: gap<=1 splits characters
    for (c0, c1) in clusters:
        sub = yellow[y0:y1 + 1, c0:c1 + 1]
        cc = sub.sum(axis=0)
        nz = np.where(cc > 0)[0]
        gl = []
        s = nz[0]
        p = nz[0]
        for x in nz[1:]:
            if x - p > 1:
                gl.append((int(s + c0), int(p + c0)))
                s = x
            p = x
        gl.append((int(s + c0), int(p + c0)))
        print(f"      cluster {c0}-{c1} width={c1-c0+1} -> glyph boxes ({len(gl)}): {gl}")
