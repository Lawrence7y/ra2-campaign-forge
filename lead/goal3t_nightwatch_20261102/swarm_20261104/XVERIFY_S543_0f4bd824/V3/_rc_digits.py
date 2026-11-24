# -*- coding: utf-8 -*-
"""RECHECK sample E: v4-b wait-trace rate, the three >=1s gaps' window spans,
and an independent read of the timer field per trip (which S543's f/31.2 table rests on).
"""
import glob
import hashlib
import json
import os

import numpy as np
from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
TBOX = (454, 121, 529, 141)   # HH:MM:SS glyph block, located by _rc_timer2.py column runs


def png_for(trip, w):
    w = int(w)
    return (os.path.join(BASE, "measure_w%d_end_x.png" % w) if trip == "<root>"
            else os.path.join(BASE, trip, "measure_w%d_end_x.png" % w))


def json_for(trip, w):
    w = int(w)
    return (os.path.join(BASE, "measure_w%d.json" % w) if trip == "<root>"
            else os.path.join(BASE, trip, "measure_w%d.json" % w))

# ---- 1. v4-b wait trace
wt = os.path.join(BASE, "l3_1101v4b", "h8_wait_trace.json")
t = json.load(open(wt, encoding="utf-8"))
print("v4-b h8_wait_trace: n=%s verdict=%s wait_s=%s samples(len)=%s"
      % (t.get("n"), t.get("verdict"), t.get("wait_s"), len(t.get("samples") or [])))
sp = t.get("samples") or []
print("  first samples:", json.dumps(sp[:3], ensure_ascii=False))
if sp and isinstance(sp[0], (list, tuple)) and len(sp[0]) == 2:
    tt = [q[0] for q in sp]
    fr = [q[1] for q in sp]
    adv = sum(1 for i in range(1, len(fr)) if fr[i] != fr[i - 1])
    fa = next((i for i in range(1, len(fr)) if fr[i] != fr[i - 1]), None)
    print("  n=%d f0=%s fN=%s n_advances=%d" % (len(fr), fr[0], fr[-1], adv))
    print("  first advance at t=%.4f (to frame %s)" % (tt[fa], fr[fa]))
    span = tt[-1] - tt[fa]
    moved = fr[-1] - fr[fa - 1]
    print("  V3's claim was 270 frames / 103.05s = 2.62 fps")
    print("  recomputed: %d frames / %.4fs = %.4f fps (from first advance)" % (moved, span, moved / span))
    print("  whole trace: %d frames / %.4fs = %.4f fps" % (fr[-1] - fr[0], tt[-1] - tt[0], (fr[-1] - fr[0]) / (tt[-1] - tt[0])))

# ---- 2. the three >=1.0s gaps: what window span are they in?
print("\n=== windows holding the only >=1.0s inter-frame gaps ===")
for trip, w in (("l1_20261023e1", 0), ("l1_20261023k", 0), ("l1_20261023hb", 0)):
    j = json.load(open(json_for(trip, w), encoding="utf-8"))
    ed = j.get("frame_edges") or []
    st = j.get("stats") or {}
    gaps = [(ed[i][1] - ed[i - 1][1], ed[i][0] - ed[i - 1][0]) for i in range(1, len(ed))]
    print("  %-16s w%d span=%s n_edges=%d df=%s fps_avg=%s p50=%s max_gap=%.3fs(step %d) max_stall=%s"
          % (trip, w, j.get("span_s"), len(ed), ed[-1][0] - ed[0][0], st.get("fps_avg"), st.get("fps_p50"),
             max(g[0] for g in gaps), max(gaps, key=lambda g: g[0])[1], st.get("max_stall_s")))

# ---- 3. timer crop hashes grouped by displayed value, per trip (which png, frame, crop sha)
print("\n=== timer-field crop sha grouping (same sha => same displayed digits, pixel-exact) ===")
groups = {}
rows = []
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png")) + glob.glob(os.path.join(BASE, "measure_w*_end_*.png"))):
    trip = os.path.basename(os.path.dirname(p))
    if trip == os.path.basename(BASE):
        trip = "<root>"
    wn = os.path.basename(p).split("measure_w")[1].split("_")[0]
    a = np.asarray(Image.open(p).convert("RGB").crop(TBOX))
    h = hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()[:10]
    jp = json_for(trip, wn)
    ed = (json.load(open(jp, encoding="utf-8")).get("frame_edges") or []) if os.path.exists(jp) else []
    f1 = ed[-1][0] if ed else None
    rows.append((trip, wn, f1, h))
    groups.setdefault(h, []).append("%s/w%s(f=%s)" % (trip, wn, f1))
for h, mem in sorted(groups.items(), key=lambda x: -len(x[1])):
    print("  %s  n=%d  %s" % (h, len(mem), "  ".join(mem)))

# ---- 4. export 8x zoom of the timer block for the trips S543's table cites
for trip, w in (("archive_T38", 2), ("archive_T39", 2), ("archive_T49_u0800", 1), ("l3_20261023r", 2)):
    p = png_for(trip, w)
    c = Image.open(p).convert("RGB").crop(TBOX)
    c = c.resize((c.width * 8, c.height * 8), Image.NEAREST)
    c.save(os.path.join(V3DIR := os.path.dirname(os.path.abspath(__file__)), "_rc_digits_%s_w%d.png" % (trip, w)))
print("\nzexports written")

# ---- 5. full-scope n_multi_advance over all 97 windows (V3 claimed 2 windows > 0)
print("\n=== step!=1 advances across ALL windows with edges (97-window scope) ===")
paths = sorted(set(glob.glob(os.path.join(BASE, "*", "measure_w*.json")) + glob.glob(os.path.join(BASE, "measure_w*.json"))))
from collections import Counter
nz = []
zero = 0
for p in paths:
    j = json.load(open(p, encoding="utf-8"))
    ed = j.get("frame_edges") or []
    if len(ed) < 2:
        continue
    steps = [ed[i][0] - ed[i - 1][0] for i in range(1, len(ed))]
    bad = [s for s in steps if s != 1]
    trip = os.path.basename(os.path.dirname(p))
    if trip == os.path.basename(BASE):
        trip = "<root>"
    if bad:
        nz.append((trip, j.get("window"), len(bad), dict(Counter(steps)),
                   (j.get("stats") or {}).get("n_multi_advance")))
    else:
        zero += 1
print("  windows with edges:", len(nz) + zero, " step-always-1:", zero, " with step!=1:", len(nz))
for x in nz:
    print("   ", x)

