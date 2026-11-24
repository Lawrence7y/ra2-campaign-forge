"""V1 probe P: whole-tree PNG census.

Goal: (1) find whether the 'artwork, no score panel' shots are duplicates of OTHER
frames in the same/other trips (which would name the screen they show),
(2) score-screen classification (title plate + 10-cell time field) applied to EVERY png
in the 14 trips that own a measure_w*_end_x.png, so the 25 shots can be placed in context,
(3) mtime vs window-end time for every shot (provenance check).
Read-only on data.
"""
import os, glob, hashlib, json
import numpy as np
from PIL import Image

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
END = sorted(glob.glob(ROOT + "/*/measure_w*_end_x.png"))
trips = sorted({p[len(ROOT) + 1:].replace("\\", "/").split("/")[0] for p in END})


def yellow(a):
    r = a[:, :, 0].astype(int); g = a[:, :, 1].astype(int); b = a[:, :, 2].astype(int)
    return (r > 170) & (g > 150) & (b < 130) & ((r - b) > 70) & ((g - b) > 50)


def ncells(m):
    sub = m[120:142, 480:545]
    cs = sub.sum(axis=0)
    n, x = 0, 0
    while x < cs.size:
        if cs[x] > 0:
            n += 1
            while x < cs.size and cs[x] > 0:
                x += 1
        else:
            x += 1
    return n


print("=== PNG census for the %d trips that own window-end shots ===" % len(trips))
pix = {}
rows = []
for trip in trips:
    for p in sorted(glob.glob(ROOT + "/" + trip + "/*.png")):
        rel = p[len(ROOT) + 1:].replace("\\", "/")
        try:
            im = Image.open(p)
            if im.size != (800, 600):
                rows.append((rel, "SIZE=%s" % (im.size,), 0, 0, None))
                continue
            a = np.asarray(im.convert("RGB"))
        except Exception as e:
            rows.append((rel, "ERR %s" % e, 0, 0, None))
            continue
        h = hashlib.sha256(a.tobytes()).hexdigest()
        m = yellow(a)
        plate = int(m[5:30, 665:760].sum())
        cn = ncells(m)
        pix.setdefault(h, []).append(rel)
        rows.append((rel, "", plate, cn, h))

print("%-58s %-9s %-6s %s" % ("file", "plate", "cells", "pixsha"))
for rel, note, plate, cn, h in rows:
    print("%-58s %-9s %-6s %s %s" % (rel, plate, cn, (h or "")[:16], note))

print()
print("=== duplicate pixel groups across ALL pngs in these trips ===")
for h, v in sorted(pix.items(), key=lambda kv: -len(kv[1])):
    if len(v) > 1:
        print("GROUP n=%d %s" % (len(v), h[:12]))
        for x in v:
            print("     ", x)

print()
print("=== provenance: shot mtime vs its window's t_abs0 + span ===")
for p in END:
    rel = p[len(ROOT) + 1:].replace("\\", "/")
    trip, fn = rel.split("/")
    jf = os.path.join(ROOT, trip, fn.replace("_end_x.png", ".json"))
    d = json.load(open(jf, encoding="utf-8"))
    end_t = d["t_abs0"] + d["span_s"]
    mt = os.path.getmtime(p)
    print("%-46s png_mtime=%d win_end=%.1f delta=%+8.1f s  %s" % (
        rel, mt, end_t, mt - end_t, "OK" if abs(mt - end_t) < 4 else "<< STALE/COPY"))
