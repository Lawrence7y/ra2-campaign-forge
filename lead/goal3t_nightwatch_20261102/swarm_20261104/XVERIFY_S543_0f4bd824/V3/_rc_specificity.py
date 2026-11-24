# -*- coding: utf-8 -*-
"""RECHECK sample F: verify V3's provenance classes and its false-positive rate.

(a) every PNG under BASE grouped by basename -> file sha + set of mtimes:
    does 'navsig_burst_04_x' really have cross-trip identical BYTES *and* identical MTIME
    (copy residue), while 'frame_target_01' has identical bytes but distinct mtimes
    (independent captures of a static screen)?
(b) recompute the p-criterion over the whole repo tree: how many control (non window-end)
    800x600 pngs also score p>=0.30 -> V3 claimed 304/1942 = 15.7%.
(c) my own fixed-text signature: rows that are pixel-identical between score screens of
    DIFFERENT trips, then how many control pngs match that signature exactly.
"""
import glob
import hashlib
import os

import numpy as np
from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
PANEL = (85, 108, 630, 275)

allpng = glob.glob(os.path.join(BASE, "**", "*.png"), recursive=True)
print("all pngs under BASE:", len(allpng))
endpng = set(os.path.abspath(p) for p in
             glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png")) + glob.glob(os.path.join(BASE, "measure_w*_end_*.png")))


def arr(p):
    try:
        im = Image.open(p).convert("RGB")
    except Exception:
        return None
    return im if im.size == (800, 600) else None


def pv(a):
    c = np.asarray(a.crop(PANEL))
    r, g, b = c[..., 0].astype(int), c[..., 1].astype(int), c[..., 2].astype(int)
    return float(((b > r + 18) & (b > g + 10) & (b >= 40) & (b <= 190) & (r < 150)).sum()) / c[..., 0].size


# ---- (a) name / sha / mtime classes
print("\n=== (a) cross-trip byte duplicates, split by whether mtime is also identical ===")
byname = {}
for p in allpng:
    n = os.path.basename(p)
    byname.setdefault(n, []).append(p)
for n, ps in sorted(byname.items(), key=lambda x: -len(x[1])):
    if len(ps) < 3:
        continue
    grp = {}
    for p in ps:
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:8]
        grp.setdefault(h, []).append((p, int(os.path.getmtime(p))))
    multi = {h: v for h, v in grp.items() if len(v) > 1}
    if not multi:
        continue
    for h, v in sorted(multi.items(), key=lambda x: -len(x[1])):
        trips = {os.path.basename(os.path.dirname(p)) for p, _ in v}
        mt = {m for _, m in v}
        cls = "COPY-RESIDUE (mtime identical)" if len(mt) == 1 and len(v) > 1 else (
            "INDEPENDENT-STATIC (mtimes all distinct)" if len(mt) == len(v) else "MIXED (%d distinct mtimes over %d files)" % (len(mt), len(v)))
        print("  %-26s sha=%s n=%d trips=%d  %s" % (n, h, len(v), len(trips), cls))

# ---- (b) p-criterion false positive rate over control pngs
print("\n=== (b) p>=0.30 on control (non window-end) 800x600 pngs ===")
ctrl = [p for p in allpng if os.path.abspath(p) not in endpng]
print("  control pngs considered:", len(ctrl))
fp = []
tp = []
for p in sorted(set(ctrl)):
    a = arr(p)
    if a is None:
        continue
    if pv(a) >= 0.30:
        fp.append(p)
for p in sorted(endpng):
    a = arr(p)
    if a is not None and pv(a) >= 0.30:
        tp.append(p)
print("  window-end pngs with p>=0.30 (true positives): %d / %d" % (len(tp), len(endpng)))
print("  control pngs with p>=0.30 (false positives)  : %d / %d = %.1f%%"
      % (len(fp), len(ctrl), 100.0 * len(fp) / max(1, len(ctrl))))
from collections import Counter
print("  which control basenames hit:", Counter(os.path.basename(x) for x in fp).most_common(8))

# ---- (c) my own fixed-text signature
print("\n=== (c) fixed-text row signature, built from score screens of 3 different trips ===")
refs = [os.path.join(BASE, "archive_T34", "measure_w1_end_x.png"),
        os.path.join(BASE, "archive_T41", "measure_w1_end_x.png"),
        os.path.join(BASE, "archive_T44", "measure_w2_end_x.png")]
arrs = [np.asarray(arr(p).crop(PANEL)) for p in refs]
H = arrs[0].shape[0]
ident_rows = [y for y in range(H) if np.array_equal(arrs[0][y], arrs[1][y]) and np.array_equal(arrs[0][y], arrs[2][y])]
print("  rows pixel-identical across 3 different trips: %d / %d" % (len(ident_rows), H))
bands, cur = [], None
for y in ident_rows:
    if cur is None or y != cur[1] + 1:
        if cur:
            bands.append(cur)
        cur = [y, y]
    else:
        cur[1] = y
if cur:
    bands.append(cur)
print("  contiguous bands (y in panel-crop coords):", bands)
sig = np.stack([arrs[0][a:b + 1] for a, b in bands])
sh = hashlib.sha256(np.ascontiguousarray(sig).tobytes()).hexdigest()[:10]
print("  signature sha:", sh)


def match(p):
    a = arr(p)
    if a is None:
        return False
    c = np.asarray(a.crop(PANEL))
    if c.shape != arrs[0].shape:
        return False
    s2 = np.stack([c[x:y + 1] for x, y in bands])
    return bool(np.array_equal(s2, sig))


sigtp = [p for p in sorted(endpng) if match(p)]
sigfp = [p for p in sorted(set(ctrl)) if match(p)]
print("  signature hits among window-end pngs : %d / %d" % (len(sigtp), len(endpng)))
for p in sigtp:
    print("      ", os.path.relpath(p, BASE))
print("  signature hits among control pngs    : %d / %d = %.1f%%" % (len(sigfp), len(ctrl), 100.0 * len(sigfp) / max(1, len(ctrl))))
for p in sigfp[:25]:
    print("      ", os.path.relpath(p, BASE))
