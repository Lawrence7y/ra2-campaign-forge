# -*- coding: utf-8 -*-
"""RECHECK sample C: read the score-panel header of T38/w2 (f=940) and T39/w2 (f=945).

V3's flagship refutation is: 940/31.2 = 30.13s and 945/31.2 = 30.29s both round to the
same integer second 30, yet the two timer bitmaps differ. To judge that I need the
ACTUAL digits, so: diff the two panels, localise where they differ, and export zooms.
"""
import os

import numpy as np
from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
V3 = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\XVERIFY_S543_0f4bd824\V3"
PANEL = (85, 108, 630, 275)

A = os.path.join(BASE, "archive_T38", "measure_w2_end_x.png")
B = os.path.join(BASE, "archive_T39", "measure_w2_end_x.png")
C = os.path.join(BASE, "archive_T36", "measure_w1_end_x.png")

ia = Image.open(A).convert("RGB")
ib = Image.open(B).convert("RGB")
ic = Image.open(C).convert("RGB")
print("sizes", ia.size, ib.size, ic.size)

a = np.asarray(ia)
b = np.asarray(ib)
d = (np.abs(a.astype(int) - b.astype(int)).sum(axis=2) > 24)
print("whole-frame differing pixels:", int(d.sum()))
ys, xs = np.where(d)
if len(ys):
    print("diff bbox x[%d..%d] y[%d..%d]" % (xs.min(), xs.max(), ys.min(), ys.max()))
    # cluster rows
    rows = sorted(set(ys.tolist()))
    groups, cur = [], [rows[0]]
    for r in rows[1:]:
        if r - cur[-1] <= 3:
            cur.append(r)
        else:
            groups.append(cur)
            cur = [r]
    groups.append(cur)
    print("diff row-bands:")
    for g in groups:
        m = (ys >= g[0]) & (ys <= g[-1])
        gx = xs[m]
        print("   y[%d..%d] x[%d..%d] npix=%d" % (g[0], g[-1], gx.min(), gx.max(), len(g)))

# export: header band of the panel, 4x, side by side for T36/T38/T39
for name, im in (("T36w1", ic), ("T38w2", ia), ("T39w2", ib)):
    c = im.crop(PANEL)
    c = c.resize((c.width * 3, c.height * 3), Image.LANCZOS)
    c.save(os.path.join(V3, "_rc_panel_%s.png" % name))
    print("saved _rc_panel_%s.png %s" % (name, c.size))

# narrow strip around the 时间 readout: rows found in the top of the panel
for name, im in (("T36w1", ic), ("T38w2", ia), ("T39w2", ib)):
    s = im.crop((85, 108, 630, 160)).resize(((630 - 85) * 5, (160 - 108) * 5), Image.LANCZOS)
    s.save(os.path.join(V3, "_rc_hdr_%s.png" % name))
print("saved header strips 5x")
