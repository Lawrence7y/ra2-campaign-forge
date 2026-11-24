"""V1 probe K: localise the w1-vs-w2 pixel changes, and build a visual diff so the
'motion' in the frozen windows can be attributed to a screen region rather than asserted.
Writes PNGs into the V1 dir only."""
import os, glob
import numpy as np
from PIL import Image

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
V1 = "D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/V1"

paths = sorted(glob.glob(ROOT + "/*/measure_w*_end_x.png"))
trips = {}
for p in paths:
    rel = p[len(ROOT) + 1:].replace("\\", "/")
    trip, fn = rel.split("/")
    trips.setdefault(trip, {})[fn.split("measure_")[1].split("_end")[0]] = rel


def band_profile(d, thresh=0):
    """d = per-pixel max abs diff (H,W). return list of (y0,y1,ncols,npx) changed row bands"""
    ch = d > thresh
    rows = np.where(ch.any(axis=1))[0]
    out = []
    if len(rows) == 0:
        return out
    s = prev = rows[0]
    for y in rows[1:]:
        if y - prev > 3:
            out.append((s, prev))
            s = y
        prev = y
    out.append((s, prev))
    res = []
    for (y0, y1) in out:
        cols = np.where(ch[y0:y1 + 1].any(axis=0))[0]
        res.append((y0, y1, int(ch[y0:y1 + 1].sum()), (int(cols.min()), int(cols.max()))))
    return res


for trip in sorted(trips):
    d = trips[trip]
    if "w1" not in d or "w2" not in d:
        continue
    a = np.asarray(Image.open(ROOT + "/" + d["w1"]).convert("RGB"))
    b = np.asarray(Image.open(ROOT + "/" + d["w2"]).convert("RGB"))
    dd = np.abs(a.astype(int) - b.astype(int)).max(axis=2)
    tot = int((dd > 0).sum())
    print("=" * 74)
    print("%s  w1 vs w2: changed px (any) = %d  >32 = %d" % (trip, tot, int((dd > 32).sum())))
    for (y0, y1, npx, (c0, c1)) in band_profile(dd):
        print("    rows %3d-%3d  cols %3d-%3d  npx=%d" % (y0, y1, c0, c1, npx))
    if 0 < tot <= 6000:
        vis = np.zeros((600, 800, 3), dtype=np.uint8)
        vis[:, :, 0] = np.clip(dd * 6, 0, 255)
        Image.fromarray(vis).save(V1 + "/V1_diff_%s_w1w2.png" % trip)
        print("    saved V1_diff_%s_w1w2.png" % trip)
