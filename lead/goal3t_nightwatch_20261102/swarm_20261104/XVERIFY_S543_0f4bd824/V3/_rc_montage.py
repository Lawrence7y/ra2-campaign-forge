# -*- coding: utf-8 -*-
"""RECHECK: (a) montage every unique timer-field crop with its window's frame number,
so the displayed seconds can be read by eye and compared to f/31.2;
(b) archive_T32 fields: how many MEASURE rows, any forensics rows at all;
(c) recompute S543's 'implied fps' band using MY OWN digit reads.
"""
import glob
import hashlib
import json
import os

import numpy as np
from PIL import Image, ImageDraw

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
V3 = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\XVERIFY_S543_0f4bd824\V3"
TBOX = (454, 121, 529, 141)
SCALE = 9


def jp_for(trip, w):
    return (os.path.join(BASE, "measure_w%d.json" % int(w)) if trip == "<root>"
            else os.path.join(BASE, trip, "measure_w%d.json" % int(w)))


rows = []
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png")) + glob.glob(os.path.join(BASE, "measure_w*_end_*.png"))):
    trip = os.path.basename(os.path.dirname(p))
    if trip == os.path.basename(BASE):
        trip = "<root>"
    wn = os.path.basename(p).split("measure_w")[1].split("_")[0]
    a = np.asarray(Image.open(p).convert("RGB").crop(TBOX))
    rows.append((hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()[:10], trip, wn,
                 Image.open(p).convert("RGB").crop(TBOX)))

# keep one representative per unique timer bitmap, but list ALL members in the label
uniq = {}
for h, trip, wn, img in rows:
    uniq.setdefault(h, []).append((trip, wn))

tiles = []
for h, members in sorted(uniq.items(), key=lambda x: -len(x[1])):
    trip, wn = members[0]
    jp = jp_for(trip, wn)
    ed = (json.load(open(jp, encoding="utf-8")).get("frame_edges") or []) if os.path.exists(jp) else []
    f1 = ed[-1][0] if ed else None
    label = "%s/w%s f=%s  [%s]" % (trip, wn, f1, ",".join("%s/w%s" % m for m in members))
    tiles.append((h, label, f1, img))

W = TBOX[2] - TBOX[0]
H = TBOX[3] - TBOX[1]
pad = 26
canvas = Image.new("RGB", (W * SCALE + 20, (H * SCALE + pad) * len(tiles) + 10), (20, 20, 20))
dr = ImageDraw.Draw(canvas)
y = 5
for h, label, f1, img in tiles:
    canvas.paste(img.resize((W * SCALE, H * SCALE), Image.NEAREST), (10, y))
    dr.text((12, y + H * SCALE + 6), "%s  %s" % (label, h), fill=(255, 255, 255))
    y += H * SCALE + pad
canvas.save(os.path.join(V3, "_rc_timer_montage.png"))
print("wrote _rc_timer_montage.png  tiles=%d  (each tile is the pixel-identical group)" % len(tiles))
for h, label, f1, img in tiles:
    print("  %s  f=%s" % (label, f1))

print("\n########## archive_T32 fields ##########")
fp = os.path.join(BASE, "archive_T32", "qc151_fields.json")
d = json.load(open(fp, encoding="utf-8"))
print(" total records:", len(d), " groups:", sorted({r.get("group") for r in d}))
meas = [r for r in d if r.get("group") == "MEASURE"]
print(" MEASURE rows:", len(meas))
for r in meas:
    print("   ", r.get("key"))
print(" forensics rows:", sum(1 for r in d if "forensic" in str(r.get("key", ""))))
pngs = glob.glob(os.path.join(BASE, "archive_T32", "*.png"))
print(" pngs in dir:", len(pngs))

print("\n########## how many end-png dirs exist for T47 / l1_20261023b? ##########")
for t in ("archive_T47", "l1_20261023b", "l1_20261023", "archive_T32"):
    d2 = json.load(open(os.path.join(BASE, t, "qc151_fields.json"), encoding="utf-8")) if os.path.exists(os.path.join(BASE, t, "qc151_fields.json")) else []
    fr = [r for r in d2 if "forensic" in str(r.get("key", ""))]
    print("  %-16s fields=%d forensics_rows=%d pngs_in_dir=%d" % (t, len(d2), len(fr), len(glob.glob(os.path.join(BASE, t, "*.png")))))
    for r in fr:
        v = r.get("value") or {}
        print("      %s empty_window=%s capture_ok=%s png=%s" % (r.get("key"), v.get("empty_window"), v.get("capture_ok"), v.get("forensics_png")))
