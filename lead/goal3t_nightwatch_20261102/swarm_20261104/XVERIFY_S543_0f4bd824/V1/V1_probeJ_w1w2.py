"""V1 probe J (v2): w1 vs w2 per-pixel diffs on the measured time field, the title plate,
the document's asserted rectangle, the score-table body and the whole frame.
Also classifies the 2 stray measure_w*_end_x.png at the trip root (data set is 27 files,
the document says 25)."""
import os, glob
import numpy as np
from PIL import Image

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
DOCBOX = (430, 118, 640, 150)     # rectangle asserted by the S543 document
FIELD = (450, 120, 535, 142)      # 时间 label + value, measured (probes B/E/H)
PLATE = (660, 3, 765, 32)         # score-screen title plate, measured (probe B)
FULL = (0, 0, 800, 600)
TABLE = (90, 180, 540, 330)       # score table body rows
GAME = (90, 100, 700, 600)


def load(rel):
    return np.asarray(Image.open(ROOT + "/" + rel).convert("RGB"))


def stats(a, b, box):
    x0, y0, x1, y1 = box
    d = np.abs(a[y0:y1, x0:x1].astype(int) - b[y0:y1, x0:x1].astype(int)).max(axis=2)
    return int(d.max()), int((d > 0).sum()), int(d.size)


paths = sorted(glob.glob(ROOT + "/*/measure_w*_end_x.png"))
trips = {}
for p in paths:
    rel = p[len(ROOT) + 1:].replace("\\", "/")
    trip, fn = rel.split("/")
    trips.setdefault(trip, {})[fn.split("measure_")[1].split("_end")[0]] = rel
print("trips with window-end shots: %d" % len(trips))

print()
print("=== STEP 5: same trip, w1 vs w2 ===")
hdr = "%-20s %-16s %-16s %-16s %-16s %-16s" % ("trip", "FIELD(time)", "DOCBOX", "PLATE", "TABLE", "FULL")
print(hdr)
for trip in sorted(trips):
    d = trips[trip]
    if "w1" not in d or "w2" not in d:
        print("%-20s only w%s present" % (trip, list(d)[0][-1]))
        continue
    a, b = load(d["w1"]), load(d["w2"])
    cells = []
    for box in (FIELD, DOCBOX, PLATE, TABLE, FULL):
        mx, nz, tot = stats(a, b, box)
        cells.append("max=%-3d nz=%-5d" % (mx, nz))
    print("%-20s %s" % (trip, " ".join("%-16s" % c for c in cells)))

print()
print("=== stray ROOT-level end shots (data set is 27 files, doc says 25) ===")
import hashlib
for fn in ("measure_w1_end_x.png", "measure_w2_end_x.png"):
    p = ROOT + "/" + fn
    if not os.path.exists(p):
        print("  MISSING", fn)
        continue
    a = load(fn)
    r, g, b = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
    ym = (r > 170) & (g > 150) & (b < 130) & ((r - b) > 70) & ((g - b) > 50)
    print("  %-24s pixsha=%s plateYellow=%d hdrRowYellow=%d colHdrYellow=%d" % (
        fn, hashlib.sha256(a.tobytes()).hexdigest()[:16], int(ym[5:30, 665:760].sum()),
        int(ym[120:142, 90:560].sum()), int(ym[156:178, 90:560].sum())))
    # cell count on the same 10-cell geometry as probe H
    sub = ym[120:142, 480:545]
    cs = sub.sum(axis=0)
    n = 0
    x = 0
    while x < cs.size:
        if cs[x] > 0:
            n += 1
            while x < cs.size and cs[x] > 0:
                x += 1
        else:
            x += 1
    print("     value-region cells = %d" % n)
