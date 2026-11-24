# -*- coding: utf-8 -*-
"""RECHECK sample G: fixed-text score-table signature specificity, plus the
disputed per-trip items (l1_20261023 / l1_20261023b / archive_T47 / archive_T32).
All paths are built by joining the fixed BASE root with literal directory names.
"""
import glob
import hashlib
import json
import os

import numpy as np
from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
V3 = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\XVERIFY_S543_0f4bd824\V3"
PANEL = (85, 108, 630, 275)
TB = (454, 121, 529, 141)

REFS = [
    os.path.join(BASE, "archive_T34", "measure_w1_end_x.png"),
    os.path.join(BASE, "archive_T41", "measure_w1_end_x.png"),
    os.path.join(BASE, "archive_T44", "measure_w2_end_x.png"),
]
arrs = [np.asarray(Image.open(p).convert("RGB").crop(PANEL)) for p in REFS]
print("reference score screens:", [os.path.relpath(p, BASE) for p in REFS])
H, Wd = arrs[0].shape[:2]
ident = [y for y in range(H) if all(np.array_equal(arrs[0][y], a[y]) for a in arrs[1:])]
bands = []
cur = None
for y in ident:
    if cur is None or y != cur[1] + 1:
        if cur:
            bands.append((cur[0], cur[1]))
        cur = [y, y]
    else:
        cur[1] = y
if cur:
    bands.append((cur[0], cur[1]))
print("rows identical across 3 different trips: %d / %d ; bands: %s" % (len(ident), H, bands))


def sig_of(crop):
    return np.concatenate([crop[a:b + 1] for a, b in bands], axis=0)


SIG = sig_of(arrs[0])
print("signature shape %s sha %s" % (SIG.shape, hashlib.sha256(np.ascontiguousarray(SIG).tobytes()).hexdigest()[:10]))


def sigmatch(path):
    try:
        im = Image.open(path).convert("RGB")
    except Exception:
        return False
    if im.size != (800, 600):
        return False
    c = np.asarray(im.crop(PANEL))
    if c.shape != arrs[0].shape:
        return False
    return bool(np.array_equal(sig_of(c), SIG))


endpng = sorted(set(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png")) +
                    glob.glob(os.path.join(BASE, "measure_w*_end_*.png"))))
endset = set(os.path.abspath(p) for p in endpng)
ctrl = sorted(set(p for p in glob.glob(os.path.join(BASE, "**", "*.png"), recursive=True)
                  if os.path.abspath(p) not in endset))

tp = [p for p in endpng if sigmatch(p)]
fp = [p for p in ctrl if sigmatch(p)]
print("\nSIGNATURE = exact fixed table rows (no colour heuristic):")
print("  window-end pngs hit : %d / %d" % (len(tp), len(endpng)))
for p in tp:
    print("      ", os.path.relpath(p, BASE))
print("  control pngs hit    : %d / %d = %.2f%%" % (len(fp), len(ctrl), 100.0 * len(fp) / max(1, len(ctrl))))
from collections import Counter
for k, v in Counter((os.path.basename(os.path.dirname(p)) + "/" + os.path.basename(p)) for p in fp).most_common(40):
    print("      %-52s %d" % (k, v))

print("\n=== the six/seven 'no window-end image' frozen windows ===")
CHECKS = [("l1_20261023", 0), ("l1_20261023b", 0), ("archive_T47", 1),
          ("archive_T47", 2), ("archive_T32", 1), ("archive_T32", 2)]
for trip, w in CHECKS:
    ep = os.path.join(BASE, trip, "measure_w%d_end_x.png" % w)
    jpp = os.path.join(BASE, trip, "measure_w%d.json" % w)
    ed = json.load(open(jpp, encoding="utf-8")).get("frame_edges") or []
    print("  %-16s w%d  end_png_on_disk=%-5s f0/f1=%s" % (trip, w, os.path.exists(ep), (ed[0][0], ed[-1][0])))

print("\n=== does each of those trips have ANY png that is a score screen? ===")
for trip in ("l1_20261023", "l1_20261023b", "archive_T47", "archive_T32"):
    hits = []
    for p in sorted(glob.glob(os.path.join(BASE, trip, "*.png"))):
        if sigmatch(p):
            hits.append(os.path.basename(p))
    print("  %-16s pngs=%3d  signature hits=%s" % (trip, len(glob.glob(os.path.join(BASE, trip, "*.png"))), hits))
    ft = os.path.join(BASE, trip, "frame_target_01.png")
    if os.path.exists(ft):
        im = Image.open(ft).convert("RGB")
        c = np.asarray(im.crop(PANEL))
        r, g, b = c[..., 0].astype(int), c[..., 1].astype(int), c[..., 2].astype(int)
        pv = float(((b > r + 18) & (b > g + 10) & (b >= 40) & (b <= 190) & (r < 150)).sum()) / c[..., 0].size
        z = im.crop(TB).resize(((TB[2] - TB[0]) * 8, (TB[3] - TB[1]) * 8), Image.NEAREST)
        z.save(os.path.join(V3, "_rc_ft_%s.png" % trip))
        print("      frame_target_01 p=%.4f sigmatch=%s  timer zoom -> _rc_ft_%s.png" % (pv, sigmatch(ft), trip))
