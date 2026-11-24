"""V1 probe Y: what are the 5 'no-panel' shots?  Region-wise identity against score screens,
plus crops for visual reading, plus identity of the trip that owns the 2 root-level shots."""
import os
import numpy as np
from PIL import Image

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
V1 = "D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/V1"

DUP = "archive_T42/measure_w1_end_x.png"
SCORES = ["archive_T33/measure_w1_end_x.png", "archive_T34/measure_w1_end_x.png",
          "archive_T44/measure_w1_end_x.png", "l3_20261023r/measure_w2_end_x.png",
          "measure_w1_end_x.png"]
REGIONS = {
    "far-left edge x0-95 (all y)": (0, 600, 0, 95),
    "top strip x95-660 y0-100": (0, 100, 95, 660),
    "table area x95-660 y100-600": (100, 600, 95, 660),
    "sidebar x660-800 y0-110": (0, 110, 660, 800),
    "sidebar slots x660-800 y110-600": (110, 600, 660, 800),
    "bottom strip x0-660 y560-600": (560, 600, 0, 660),
}
d = np.asarray(Image.open(ROOT + "/" + DUP).convert("RGB")).astype(int)
print("=== 'no-panel' shot %s vs score screens, region-wise pixel identity ===" % DUP)
print("%-38s %s" % ("region", " ".join("%-14s" % s.split("/")[0][:13] for s in SCORES)))
for name, (y0, y1, x0, x1) in REGIONS.items():
    fr = []
    for s in SCORES:
        a = np.asarray(Image.open(ROOT + "/" + s).convert("RGB")).astype(int)
        dd = np.abs(a[y0:y1, x0:x1] - d[y0:y1, x0:x1]).max(axis=2)
        fr.append("%.1f%%" % (100.0 * (dd == 0).mean()))
    print("%-38s %s" % (name, " ".join("%-14s" % x for x in fr)))

print()
print("=== crops for visual reading: DUP (left) vs T33/w1 score (right) ===")
for tag, box in [("slots", (655, 110, 800, 600)), ("tablearea", (95, 100, 660, 600))]:
    a = Image.open(ROOT + "/archive_T33/measure_w1_end_x.png").convert("RGB").crop(box)
    b = Image.open(ROOT + "/" + DUP).convert("RGB").crop(box)
    sc = 2 if (box[2] - box[0]) > 300 else 4
    a = a.resize((a.width * sc, a.height * sc), Image.NEAREST)
    b = b.resize((b.width * sc, b.height * sc), Image.NEAREST)
    o = Image.new("RGB", (a.width * 2 + 10, a.height), (40, 40, 40))
    o.paste(a, (0, 0)); o.paste(b, (a.width + 10, 0))
    o.save(V1 + "/V1_cmpY_%s_score_left_dup_right.png" % tag)
    print("   saved V1_cmpY_%s_*.png %s (left=score screen T33/w1, right=no-panel T42/w1)" % (tag, o.size))

print()
print("=== the trip that owns the two ROOT-level shots ===")
for w in (0, 1, 2):
    j = ROOT + "/measure_w%d.json" % w
    if os.path.exists(j):
        dd = json_load = __import__("json").load(open(j, encoding="utf-8"))
        print("   measure_w%d: trip_id=%s map_sha=%s gamemd=%s gate=%s verdict=%s edges=%s" % (
            w, dd.get("trip_id"), (dd.get("map_sha256") or "")[:12], (dd.get("gamemd_sha256") or "")[:12],
            dd.get("gate"), dd.get("verdict"), (dd.get("frame_edges") or [])[:3]))

print()
print("=== l1_20261023e4/measure_w2_end_x.png  (the 5th non-score shot) ===")
L = np.asarray(Image.open(ROOT + "/l1_20261023e4/measure_w2_end_x.png").convert("RGB"))
print("   mean colour", L.reshape(-1, 3).mean(0).round(1), " unique colours:", len(np.unique(L.reshape(-1, 3), axis=0)))
for y in (0, 60, 120, 180, 240, 300, 360, 420, 480, 540, 598):
    print("   row %3d colours: %s" % (y, np.unique(L[y].reshape(-1, 3), axis=0)[:5]))
Image.open(ROOT + "/l1_20261023e4/measure_w2_end_x.png").save(V1 + "/V1_cmpY_l1_20261023e4_w2.png")
print("   saved V1_cmpY_l1_20261023e4_w2.png")
