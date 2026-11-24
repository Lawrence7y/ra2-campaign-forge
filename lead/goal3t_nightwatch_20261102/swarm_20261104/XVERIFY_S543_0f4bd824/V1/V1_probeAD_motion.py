"""V1 probe AD (v2): characterise the pixels that change between w1 and w2 of one trip.

Is the score screen really 'not updating' (document's wording)? Print, per region,
how many pixels differ and show a couple of concrete before/after colours.
"""
import numpy as np
from PIL import Image

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
REG = [(9, 24, 735, 758, "title-plate tail"),
       (47, 100, 671, 763, "sidebar inset box"),
       (124, 139, 95, 535, "hdr row (游戏/时间)"),
       (160, 175, 95, 535, "column headers"),
       (196, 210, 95, 535, "table row 1"),
       (233, 247, 95, 535, "table row 2"),
       (270, 290, 95, 535, "table row 3")]

for trip in ["archive_T34", "archive_T36", "archive_T41", "archive_T44", "archive_T49_u0800", "archive_T38"]:
    a = np.asarray(Image.open("%s/%s/measure_w1_end_x.png" % (ROOT, trip)).convert("RGB")).astype(int)
    b = np.asarray(Image.open("%s/%s/measure_w2_end_x.png" % (ROOT, trip)).convert("RGB")).astype(int)
    print("=" * 72)
    print(trip, " w1 vs w2")
    for (y0, y1, x0, x1, tag) in REG:
        d = np.abs(a[y0:y1, x0:x1] - b[y0:y1, x0:x1]).max(axis=2)
        n = int((d > 0).sum())
        where = ""
        if n:
            ys, xs = np.where(d > 0)
            where = "rows %d-%d cols %d-%d" % (y0 + ys.min(), y0 + ys.max(), x0 + xs.min(), x0 + xs.max())
            big = np.argsort(-d.ravel())[:3]
            s = []
            for j in big:
                yy, xx = int(j) // d.shape[1], int(j) % d.shape[1]
                s.append("(%d,%d)%s->%s" % (y0 + yy, x0 + xx, tuple(a[y0 + yy, x0 + xx]), tuple(b[y0 + yy, x0 + xx])))
            where += "  e.g. " + "; ".join(s)
        print("  %-20s changed=%5d/%5d  max=%3d  %s" % (tag, n, d.size, int(d.max()), where))
