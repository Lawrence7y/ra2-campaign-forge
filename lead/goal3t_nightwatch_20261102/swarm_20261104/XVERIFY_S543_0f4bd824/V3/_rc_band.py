# -*- coding: utf-8 -*-
"""RECHECK: legible 6x crops of the timer box, one file per image, plus a byte-level
cross-check: if S543 says T38 and T40 both read 00:00:30, their timer crops must be
pixel-identical. Compare crop hashes to each claimed second.
"""
import hashlib
import json
import os

import numpy as np
from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
V3 = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\XVERIFY_S543_0f4bd824\V3"
TBOX = (454, 121, 529, 141)

CLAIM = {  # seconds S543's table §二 asserts for each trip
    "archive_T33": 24, "archive_T34": 10, "archive_T36": 10, "archive_T38": 30,
    "archive_T39": 31, "archive_T40": 30, "archive_T41": 28, "archive_T43": 10,
    "archive_T44": 29, "archive_T45": 28, "archive_T49_u0800": 15, "l3_20261023r": 176,
}

print("=== byte-level test of S543's §二 table: same claimed second => same timer bitmap ===")
groups = {}
for trip, sec in CLAIM.items():
    for w in (1, 2):
        p = (os.path.join(BASE, "measure_w%d_end_x.png" % w) if trip == "<root>"
             else os.path.join(BASE, trip, "measure_w%d_end_x.png" % w))
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB")
        a = np.asarray(im.crop(TBOX))
        h = hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()[:10]
        ed = (json.load(open(os.path.join(BASE, trip, "measure_w%d.json" % w), encoding="utf-8")).get("frame_edges") or [])
        f = ed[-1][0] if ed else None
        groups.setdefault(h, []).append((trip, w, f, sec))
        if len(groups[h]) == 1:
            c = im.crop(TBOX)
            c = c.resize((c.width * 6, c.height * 6), Image.NEAREST)
            c.save(os.path.join(V3, "_rc_t6_%s_w%d.png" % (trip, w)))

for h, mem in sorted(groups.items(), key=lambda x: x[1][0][3]):
    secs = sorted({m[3] for m in mem})
    print("  bitmap %s  claimed-seconds=%s  members=%s" % (h, secs, ["%s/w%d f=%s" % (m[0], m[1], m[2]) for m in mem]))

print("\n  => if a single bitmap is tagged with TWO different claimed seconds,")
print("     at least one of those readings in S543's §二 table is wrong.")

print("\n=== frame/second implied fps, using S543's own claimed seconds ===")
for h, mem in sorted(groups.items(), key=lambda x: x[1][0][3]):
    for trip, w, f, sec in mem:
        if f and sec:
            print("   %-20s w%d f=%-6s sec=%-4s implied=%7.3f  in29.9-31.4=%s"
                  % (trip, w, f, sec, f / sec, 29.9 <= f / sec <= 31.4))
