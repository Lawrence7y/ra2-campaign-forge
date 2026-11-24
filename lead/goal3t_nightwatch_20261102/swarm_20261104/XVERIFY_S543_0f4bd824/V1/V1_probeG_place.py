"""V1 probe G: exact glyph placement + global offset search (read-only)."""
import os
import numpy as np
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
P = lambda r: os.path.join(ROOT, r.replace("/", os.sep))


def yellow(a):
    r = a[:, :, 0].astype(int); g = a[:, :, 1].astype(int); b = a[:, :, 2].astype(int)
    return (r > 170) & (g > 150) & (b < 130) & ((r - b) > 70) & ((g - b) > 50)


for rel in ["archive_T33/measure_w1_end_x.png", "archive_T34/measure_w1_end_x.png",
            "archive_T38/measure_w1_end_x.png", "archive_T39/measure_w2_end_x.png",
            "l3_20261023r/measure_w2_end_x.png"]:
    a = np.asarray(Image.open(P(rel)).convert("RGB"))
    m = yellow(a)
    band = m[125:137, 450:540]
    prof = band.sum(axis=0)
    print("== %s" % rel)
    print("   col:", "".join("%4d" % (450 + i) for i in range(0, 90, 5)))
    print("   ink:", "".join("%4d" % int(prof[i]) if prof[i] else "   ." for i in range(0, 90, 5)))
    print("   full ink row (cols 450..539):",
          "".join(str(int(v)) if v else "." for v in prof))

A = np.asarray(Image.open(P("archive_T33/measure_w1_end_x.png")).convert("RGB")).astype(int)
B = np.asarray(Image.open(P("archive_T34/measure_w1_end_x.png")).convert("RGB")).astype(int)
print()
print("== global offset search: fraction of exactly-equal RGB pixels, T33/w1 vs T34/w1")
res = []
for dy in range(-2, 3):
    for dx in range(-2, 3):
        y0a, y0b = (dy, 0) if dy >= 0 else (0, -dy)
        x0a, x0b = (dx, 0) if dx >= 0 else (0, -dx)
        hh, ww = 600 - abs(dy), 800 - abs(dx)
        eq = float((A[y0a:y0a + hh, x0a:x0a + ww] == B[y0b:y0b + hh, x0b:x0b + ww]).all(axis=2).mean())
        res.append((eq, dx, dy))
res.sort(reverse=True)
for eq, dx, dy in res[:6]:
    print("   dx=%+d dy=%+d identical-pixel-frac=%.5f" % (dx, dy, eq))
zero = [e for e, x, y in res if x == 0 and y == 0][0]
print("   note: dx=0,dy=0 frac=%.5f" % zero)
