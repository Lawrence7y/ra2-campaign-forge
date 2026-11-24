"""V1 probe B: locate the yellow text pixels (RA2 HUD yellow) on a few reference
screenshots, so that the 'time' field region can be established from pixels, not
from the original document's guess. Read-only on data; crops written to V1 dir."""
import os
import numpy as np
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
OUT = r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/V1"

REFS = ["l3_20261023r/measure_w2_end_x.png",
        "archive_T33/measure_w1_end_x.png",
        "archive_T42/measure_w1_end_x.png",
        "l1_20261023e4/measure_w2_end_x.png"]


def yellow_mask(a):
    r = a[:, :, 0].astype(int)
    g = a[:, :, 1].astype(int)
    b = a[:, :, 2].astype(int)
    # RA2 HUD yellow: high R, high G, low-ish B
    return (r > 170) & (g > 150) & (b < 130) & ((r - b) > 70) & ((g - b) > 50)


def components(mask, minpx=12):
    """crude row/col projection clustering -> bounding boxes"""
    from scipy import ndimage  # may be unavailable
    lab, n = ndimage.label(mask)
    out = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(ys) >= minpx:
            out.append((int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()), len(ys)))
    return out


for rel in REFS:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    im = Image.open(p).convert("RGB")
    a = np.asarray(im)
    m = yellow_mask(a)
    print("=" * 70)
    print(rel, "size", im.size, "yellow px:", int(m.sum()), "yellow frac %.4f" % (m.sum() / m.size))
    # row profile: where are yellow rows?
    rows = np.where(m.sum(axis=1) > 0)[0]
    # group contiguous rows
    groups = []
    if len(rows):
        start = prev = rows[0]
        for y in rows[1:]:
            if y - prev > 4:
                groups.append((start, prev))
                start = y
            prev = y
        groups.append((start, prev))
    for (y0, y1) in groups:
        band = m[y0:y1 + 1]
        xs = np.where(band.sum(axis=0) > 0)[0]
        print("   yellow band rows %3d-%3d (h=%2d)  cols %3d-%3d  px=%d" % (
            y0, y1, y1 - y0 + 1, xs.min(), xs.max(), int(band.sum())))
    im.save(os.path.join(OUT, "V1_ref_" + rel.replace("/", "_").replace(".png", "") + ".png"))
