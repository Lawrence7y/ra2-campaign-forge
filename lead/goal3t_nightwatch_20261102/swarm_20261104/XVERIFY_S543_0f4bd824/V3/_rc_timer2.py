# -*- coding: utf-8 -*-
"""RECHECK sample D: locate the timer field myself, then re-test evidence 2
(w1 vs w2 timer identity per trip) and S543's f/31.2 table, plus V3's 23-window
redefinition of target-1 and the v4-b wait-trace rate.
"""
import glob
import json
import os

import numpy as np
from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
V3 = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\XVERIFY_S543_0f4bd824\V3"
import hashlib


def load(p):
    return np.asarray(Image.open(p).convert("RGB"))


def png_for(trip, w):
    if trip == "<root>":
        return os.path.join(BASE, "measure_w%d_end_x.png" % w)
    return os.path.join(BASE, trip, "measure_w%d_end_x.png" % w)


def json_for(trip, w):
    if trip == "<root>":
        return os.path.join(BASE, "measure_w%d.json" % w)
    return os.path.join(BASE, trip, "measure_w%d.json" % w)


# --- 1. locate the HH:MM:SS digits by finding yellow glyph pixels in the panel header row
ref = load(png_for("archive_T38", 2))
hdr = ref[108:150, 85:630]
r, g, b = hdr[..., 0].astype(int), hdr[..., 1].astype(int), hdr[..., 2].astype(int)
ym = (r > 170) & (g > 150) & (b < 120)
ys, xs = np.where(ym)
print("header yellow px:", ym.sum())
cols = sorted(set(xs.tolist()))
# column occupancy -> find the run(s) of glyph columns
occ = [int(ym[:, x].sum()) for x in range(hdr.shape[1])]
runs, cur = [], None
for x, o in enumerate(occ):
    if o > 0 and cur is None:
        cur = [x, x]
    elif o > 0:
        cur[1] = x
    elif cur is not None and x - cur[1] > 6:
        runs.append(tuple(cur))
        cur = None
if cur:
    runs.append(tuple(cur))
print("glyph column runs (in panel-crop coords, +85 for full frame):", runs)
print("glyph row extent y[%d..%d] (+108)" % (ys.min(), ys.max()))

TX0, TX1 = xs.min() + 85 - 3, xs.max() + 85 + 4
TY0, TY1 = ys.min() + 108 - 3, ys.max() + 108 + 4
print("TIMER box chosen: x[%d..%d] y[%d..%d]  w=%d h=%d" % (TX0, TX1, TY0, TY1, TX1 - TX0, TY1 - TY0))

# sanity: render the timer box of 4 known images as ASCII to read the digits myself
for trip, w, tag in (("archive_T38", 2, "T38/w2 f=940"), ("archive_T39", 2, "T39/w2 f=945"),
                     ("archive_T36", 1, "T36/w1 f=310 (==T38/w1 file)"), ("l3_20261023r", 2, "l3_20261023r/w2 f=4367"),
                     ("archive_T49_u0800", 1, "T49/w1 f=448")):
    a = load(png_for(trip, w))[TY0:TY1, TX0:TX1]
    rr, gg, bb = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    m = (rr > 170) & (gg > 150) & (bb < 120)
    print("\n--- %s  timer ascii (yellow glyph mask) ---" % tag)
    for row in m:
        print("   " + "".join("#" if v else "." for v in row))

print("\n\n########## 2. w1 vs w2 timer identity, every trip with BOTH end pngs ##########")
trips = sorted({os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png"))})
trips.append("<root>")
same = diff = 0
for t in trips:
    p1, p2 = png_for(t, 1), png_for(t, 2)
    if not (os.path.exists(p1) and os.path.exists(p2)):
        continue
    a1, a2 = load(p1)[TY0:TY1, TX0:TX1], load(p2)[TY0:TY1, TX0:TX1]
    h1 = hashlib.sha256(np.ascontiguousarray(a1).tobytes()).hexdigest()[:10]
    h2 = hashlib.sha256(np.ascontiguousarray(a2).tobytes()).hexdigest()[:10]
    f1 = (json.load(open(json_for(t, 1), encoding="utf-8")).get("frame_edges") or [[None]])[-1][0]
    f2 = (json.load(open(json_for(t, 2), encoding="utf-8")).get("frame_edges") or [[None]])[-1][0]
    s = "SAME" if h1 == h2 else "DIFF"
    same += h1 == h2
    diff += h1 != h2
    print("  %-20s w1f=%-6s w2f=%-6s timer %s  (%s / %s)" % (t, f1, f2, s, h1, h2))
print("  => SAME=%d DIFF=%d" % (same, diff))

print("\n########## 3. S543's f/31.2 table vs my own timer reads ##########")
mine = {"archive_T38": 32, "archive_T39": 31}   # digits I just read in the ASCII above
for trip in ("archive_T33", "archive_T34", "archive_T36", "archive_T40", "archive_T41",
             "archive_T43", "archive_T44", "archive_T45", "archive_T49_u0800", "l3_20261023r"):
    p = png_for(trip, 1) if os.path.exists(png_for(trip, 1)) else png_for(trip, 2)
    a = load(p)[TY0:TY1, TX0:TX1]
    print("  %-20s timer crop sha=%s" % (trip, hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()[:10]))

print("\n########## 4. V3's 23-window redefinition of target-1 ##########")
paths = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json")) + glob.glob(os.path.join(BASE, "measure_w*.json")))
sel = []
for p in paths:
    j = json.load(open(p, encoding="utf-8"))
    ed = j.get("frame_edges") or []
    if len(ed) < 2:
        continue
    st = j.get("stats") or {}
    if (ed[-1][0] - ed[0][0]) <= 0:
        continue
    gaps = [ed[i][1] - ed[i - 1][1] for i in range(1, len(ed))]
    p50 = st.get("fps_p50")
    if p50 is None:
        continue
    if max(gaps) < 1.0 and p50 < 28:
        trip = os.path.basename(os.path.dirname(p))
        sel.append((p50, trip, j.get("window"), ed[-1][0] - ed[0][0], j.get("verdict"), j.get("span_s")))
sel.sort()
print("  count =", len(sel))
for s in sel:
    print("    p50=%-7s %-20s w%s df=%-5s verdict=%-12s span=%s" % s)

# which of those 23 belong to trips that ever showed a score screen?
score_trips = set()
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png")) + glob.glob(os.path.join(BASE, "measure_w*_end_*.png"))):
    a = np.asarray(Image.open(p).convert("RGB").crop((85, 108, 630, 275)))
    rr, gg, bb = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    if float(((bb > rr + 18) & (bb > gg + 10) & (bb >= 40) & (bb <= 190) & (rr < 150)).sum()) / a[..., 0].size >= 0.30:
        score_trips.add(os.path.basename(os.path.dirname(p)))
print("  trips that ever showed a score screen (p>=0.30):", sorted(score_trips))
overlap = [s for s in sel if s[1] in score_trips]
print("  of the %d target-1 windows, %d belong to a score-screen trip" % (len(sel), len(overlap)))
for s in overlap:
    print("    ", s)
