# -*- coding: utf-8 -*-
"""RECHECK sample B: timer field, recomputed with MY OWN crops and hashes.

Targets: archive_T38/w2 (f=940) vs archive_T39/w2 (f=945) -- V3's flagship
"monotonicity violation". Also T33/w1, T34/w1, T34/w2, T36/w1, T36/w2,
<root>/w1, <root>/w2, l3_20261023r/w2 for the p-census.

Steps:
 1. locate the HH:MM:SS field by finding the brightest yellow-ish glyph run inside
    the score panel header band (no hard-coded x from V3);
 2. hash (a) whole image, (b) the located time field box, (c) the yellow-pixel
    mask inside that box;
 3. export 4x nearest-neighbour zooms so the digits can be read by eye.
Read-only on the trip tree; all writes inside V3/.
"""
import hashlib
import json
import os

import numpy as np
from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
V3 = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\XVERIFY_S543_0f4bd824\V3"

TARGETS = [
    ("archive_T33", 1), ("archive_T34", 1), ("archive_T34", 2),
    ("archive_T36", 1), ("archive_T36", 2),
    ("archive_T38", 2), ("archive_T39", 2),
    ("archive_T40", 1), ("archive_T44", 1),
    ("l3_20261023r", 2),
]


def p(path):
    if os.path.basename(os.path.dirname(path)) == os.path.basename(BASE):
        return path
    return path


def png_path(trip, w):
    if trip == "<root>":
        return os.path.join(BASE, "measure_w%d_end_x.png" % w)
    return os.path.join(BASE, trip, "measure_w%d_end_x.png" % w)


def json_path(trip, w):
    if trip == "<root>":
        return os.path.join(BASE, "measure_w%d.json" % w)
    return os.path.join(BASE, trip, "measure_w%d.json" % w)


def last_frame(trip, w):
    j = json.load(open(json_path(trip, w), encoding="utf-8"))
    ed = j.get("frame_edges") or []
    return (ed[-1][0] if ed else None), (j.get("stats") or {}).get("logic_frames"), \
        len(ed), (j.get("stats") or {}).get("fps_avg"), (j.get("stats") or {}).get("fps_p50")


def yellow_mask(a):
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    return (r > 150) & (g > 130) & (b < 120) & (np.abs(r - g) < 90)


for trip, w in TARGETS:
    pp = p(png_path(trip, w))
    if not os.path.exists(pp):
        print("MISSING PNG", trip, w)
        continue
    im = Image.open(pp).convert("RGB")
    a = np.asarray(im)
    f1, lf, ne, fpsa, fpsp = last_frame(trip, w)
    ym = yellow_mask(a)
    # bounding box of all yellow pixels (the score screen's digits are the yellow thing)
    ys, xs = np.where(ym)
    print("\n=== %s/w%d  png=%s" % (trip, w, os.path.basename(pp)))
    print("    size=%s  f1=%s logic_frames=%s n_edges=%s fps_avg=%s p50=%s  yellow_px=%d"
          % (im.size, f1, lf, ne, fpsa, fpsp, ym.sum()))
    if ym.sum() == 0:
        continue
    print("    yellow bbox x[%d..%d] y[%d..%d]" % (xs.min(), xs.max(), ys.min(), ys.max()))
    whole = hashlib.sha256(a.tobytes()).hexdigest()[:10]
    print("    whole-image pixel sha : %s" % whole)
    # export 4x zoom of the yellow bbox band for eye reading
    x0, x1 = max(0, xs.min() - 12), min(a.shape[1], xs.max() + 12)
    y0, y1 = max(0, ys.min() - 10), min(a.shape[0], ys.max() + 10)
    crop = im.crop((x0, y0, x1, y1)).resize(((x1 - x0) * 4, (y1 - y0) * 4), Image.NEAREST)
    tag = "%s_w%d" % (trip, w)
    crop.save(os.path.join(V3, "_rc_zoom_%s.png" % tag))
    print("    zoom -> _rc_zoom_%s.png  box=(%d,%d,%d,%d)" % (tag, x0, y0, x1, y1))

# the specific head-to-head V3 rests its REFUTED on
print("\n\n########## HEAD-TO-HEAD: T38/w2 (f=940) vs T39/w2 (f=945) ##########")
pair = []
for trip in ("archive_T38", "archive_T39"):
    pp = p(png_path(trip, 2))
    a = np.asarray(Image.open(pp).convert("RGB"))
    ym = yellow_mask(a)
    ys, xs = np.where(ym)
    # per-row yellow profile inside the header band only (top 45% of yellow span)
    band = ym[ys.min():ys.min() + 22, xs.min():xs.max() + 1]
    print("%s/w2  yellow bbox x[%d..%d] y[%d..%d] count=%d" % (trip, xs.min(), xs.max(), ys.min(), ys.max(), ym.sum()))
    print("   band mask sha=%s  band pixel sha=%s" % (
        hashlib.sha256(np.ascontiguousarray(band).tobytes()).hexdigest()[:10],
        hashlib.sha256(np.ascontiguousarray(a[ys.min():ys.min() + 22, xs.min():xs.max() + 1]).tobytes()).hexdigest()[:10]))
    pair.append((trip, a, ys, xs))

# do the two header bands even have the same yellow geometry? print column occupancy
for trip, a, ys, xs in pair:
    sub = yellow_mask(a)[ys.min():ys.min() + 22, :]
    occ = "".join("#" if sub[:, x].sum() > 0 else "." for x in range(sub.shape[1]))
    print(trip, "cols:", occ[:700])
