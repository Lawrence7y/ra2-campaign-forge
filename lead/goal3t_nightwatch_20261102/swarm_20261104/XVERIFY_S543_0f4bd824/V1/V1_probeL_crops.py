"""V1 probe L: crops of (a) the right-sidebar inset display that changes between w1 and w2
(rows 47-99, cols 671-762), (b) the title-plate tail that changes (rows 9-23, cols 739-753),
(c) the score-table body.  Read-only on data; PNGs written into the V1 dir."""
import os
from PIL import Image

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261103/lead/qc161_u0400_trip"
V1 = "D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/V1"

CASES = [("archive_T34", (660, 0, 775, 110), "sidebar_inset"),
         ("archive_T34", (90, 185, 545, 280), "table_body"),
         ("archive_T34", (660, 0, 775, 35), "plate"),
         ("archive_T40", (90, 185, 545, 280), "table_body"),
         ("archive_T41", (90, 185, 545, 280), "table_body"),
         ("archive_T44", (90, 185, 545, 280), "table_body"),
         ("archive_T49_u0800", (90, 185, 545, 280), "table_body"),
         ("archive_T33", (90, 185, 545, 280), "table_body"),
         ("l3_20261023r", (90, 185, 560, 300), "table_body")]

for trip, box, name in CASES:
    for w in ("w1", "w2"):
        p = "%s/%s/measure_%s_end_x.png" % (ROOT, trip, w)
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB")
        c = im.crop(box)
        scale = max(1, min(6, 1100 // max(c.width, 1)))
        c = c.resize((c.width * scale, c.height * scale), Image.NEAREST)
        out = "%s/V1_cropL_%s_%s_%s.png" % (V1, trip, w, name)
        c.save(out)
        print("saved %-58s box=%s scale=%d size=%s" % (os.path.basename(out), box, scale, c.size))
