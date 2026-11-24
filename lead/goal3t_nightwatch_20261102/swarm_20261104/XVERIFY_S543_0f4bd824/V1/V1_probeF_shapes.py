"""V1 probe F: fully pixel-derived reader for the score-screen 时间 field.

Fixed geometry established from the bitmaps printed by V1_probeE_out.txt:
  label '时间' cells at cols 454-468 and 470-483, colon at 485-486,
  value glyph slots: 488-492, 494-498, 500-501(:), 503-507, 509-513, 515-516(:), 518-522, 524-528
  digit rows: 127-135 (9 rows x 5 cols).

This script does NOT OCR. It extracts each slot's HUD-yellow bitmap, hashes it, groups
identical bitmaps across all images, and prints every distinct bitmap as ASCII so the
label of each shape is assigned by reading the printed bitmap once, then applied
mechanically to every image.
"""
import os, glob
import numpy as np
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
files = sorted(glob.glob(os.path.join(ROOT, "*", "measure_w*_end_x.png")))

SLOTS = [488, 494, 500, 503, 509, 515, 518, 524]   # start col of each of the 8 value slots
WID = [5, 5, 2, 5, 5, 2, 5, 5]
Y0, Y1 = 127, 136      # digit rows 127..135


def yellow(a):
    r = a[:, :, 0].astype(int); g = a[:, :, 1].astype(int); b = a[:, :, 2].astype(int)
    return (r > 170) & (g > 150) & (b < 130) & ((r - b) > 70) & ((g - b) > 50)


def slot_bits(m, i):
    x0, w = SLOTS[i], WID[i]
    return np.asarray(m[Y0:Y1, x0:x0 + w])


def sig(bits):
    return "".join("1" if v else "0" for v in bits.ravel())


print("### per-image raw slot bitmaps (rows printed only for slot 0..7 in compact sig form)")
allsigs = {}
for f in files:
    rel = f[len(ROOT) + 1:].replace("\\", "/")
    a = np.asarray(Image.open(f).convert("RGB"))
    m = yellow(a)
    tp = int(m[5:30, 665:760].sum())
    sigs = [sig(slot_bits(m, i)) for i in range(8)]
    print("%-45s plate=%3d  %s" % (rel, tp, " ".join(sigs)))
    for i, s in enumerate(sigs):
        allsigs.setdefault((i, s), []).append(rel)

print()
print("### distinct bitmap shapes per slot (all images), printed as ASCII")
for i in range(8):
    shapes = {s: v for (si, s), v in allsigs.items() if si == i}
    print("--- slot %d (cols %d-%d) : %d distinct shapes ---" % (i, SLOTS[i], SLOTS[i] + WID[i] - 1, len(shapes)))
    for s, v in sorted(shapes.items(), key=lambda kv: -len(kv[1])):
        w = WID[i]
        print("   shape %s  used %d times, e.g. %s" % (s[:12] + "...", len(v), v[0]))
        for r in range(Y1 - Y0):
            row = s[r * w:(r + 1) * w]
            print("        " + "".join("#" if c == "1" else "." for c in row))
