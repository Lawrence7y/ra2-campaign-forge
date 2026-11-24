# -*- coding: utf-8 -*-
"""RECHECK: root-level scope, v4-b, the 4 'duplicate' pngs, panel_p on all 27.

1. the 3 root-level windows + 2 root-level pngs that V3's 94/29-scope never counted;
2. l3_1101v4b measure_w0.json verdict / edges / stats, and h8_wait_trace rate;
3. fields records for T33/w2,T42/w1,T42/w2,T45/w2 (empty_window, capture_ok);
4. panel_p (S543's own criterion, crop (85,108,630,275)) for all 27 end pngs.
"""
import glob
import json
import os

import numpy as np
from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
V3 = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\XVERIFY_S543_0f4bd824\V3"

print("########## 1. ROOT-LEVEL windows ##########")
for w in (0, 1, 2):
    p = os.path.join(BASE, "measure_w%d.json" % w)
    j = json.load(open(p, encoding="utf-8"))
    ed = j.get("frame_edges") or []
    st = j.get("stats") or {}
    png = os.path.join(BASE, "measure_w%d_end_x.png" % w)
    print(" w%d trip_id=%-20s f0=%s f1=%s df=%s span=%s verdict=%-12s fps_avg=%s p50=%s stall=%s"
          % (w, j.get("trip_id"), ed[0][0] if ed else None, ed[-1][0] if ed else None,
             (ed[-1][0] - ed[0][0]) if ed else None, j.get("span_s"), j.get("verdict"),
             st.get("fps_avg"), st.get("fps_p50"), st.get("max_stall_s")))
    print("     end_png exists:", os.path.exists(png))
    if os.path.exists(png):
        im = Image.open(png).convert("RGB")
        a = np.asarray(im.crop((85, 108, 630, 275)))
        r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
        hit = int(((b > r + 18) & (b > g + 10) & (b >= 40) & (b <= 190) & (r < 150)).sum())
        print("     panel_p=%.4f  (>=0.30 -> score screen by S543's own criterion)" % (hit / a[..., 0].size))
        im.save(os.path.join(V3, "_rc_root_w%d.png" % w))

print("\n########## 2. l3_1101v4b ##########")
p = os.path.join(BASE, "l3_1101v4b", "measure_w0.json")
j = json.load(open(p, encoding="utf-8"))
print(" verdict=%s" % j.get("verdict"))
print(" error=%s" % j.get("error"))
print(" frame_edges=%r  len=%d" % ((j.get("frame_edges") or [])[:3], len(j.get("frame_edges") or [])))
print(" stats=%r" % (j.get("stats"),))
print(" gate=%r" % (j.get("gate"),))
print(" h8=%r" % (json.dumps(j.get("h8"), ensure_ascii=False)[:300] if j.get("h8") else None,))
wt = os.path.join(BASE, "l3_1101v4b", "h8_wait_trace.json")
print(" wait trace exists:", os.path.exists(wt))
if os.path.exists(wt):
    t = json.load(open(wt, encoding="utf-8"))
    print(" keys:", list(t)[:12] if isinstance(t, dict) else "list len %d" % len(t))
    pts = t.get("points") if isinstance(t, dict) else t
    if isinstance(pts, list) and pts:
        first = pts[0]
        kframe = "frame" if isinstance(first, dict) and "frame" in first else None
        kt = "t" if isinstance(first, dict) and "t" in first else ("time" if isinstance(first, dict) else None)
        print(" sample point:", json.dumps(first, ensure_ascii=False)[:200])
        fr = [q[kframe] for q in pts if isinstance(q, dict)] if kframe else []
        tt = [q[kt] for q in pts if isinstance(q, dict)] if kt else []
        if fr:
            adv = sum(1 for i in range(1, len(fr)) if fr[i] != fr[i - 1])
            first_adv = next((i for i in range(1, len(fr)) if fr[i] != fr[i - 1]), None)
            print(" n_points=%d frame0=%s frameN=%s n_advances=%d" % (len(fr), fr[0], fr[-1], adv))
            if first_adv is not None:
                print(" first advance at t=%.4f -> %.3f ; last t=%.4f" % (tt[first_adv], fr[first_adv] - fr[first_adv - 1], tt[-1]))
            span = tt[-1] - tt[first_adv]
            print(" frames moved after first advance = %d over %.4fs -> %.3f fps"
                  % (fr[-1] - fr[first_adv - 1], span, (fr[-1] - fr[first_adv - 1]) / span if span else -1))
            print(" full-window: %d frames over %.4fs -> %.3f fps" % (fr[-1] - fr[0], tt[-1] - tt[0], (fr[-1] - fr[0]) / (tt[-1] - tt[0])))

print("\n########## 3. the four byte-identical pngs: harness records ##########")
for trip, w in (("archive_T33", 2), ("archive_T42", 1), ("archive_T42", 2), ("archive_T45", 2)):
    fp = os.path.join(BASE, trip, "qc151_fields.json")
    d = json.load(open(fp, encoding="utf-8"))
    for r in d:
        v = r.get("value") or {}
        if r.get("key") == "measure_forensics_w%d" % w if isinstance(r.get("key"), str) else False:
            pass
    for r in d:
        if str(r.get("key", "")).endswith("measure_forensics_w%d" % w):
            v = r.get("value") or {}
            print(" %-14s w%d window=%s empty_window=%s capture_ok=%s png=%s cur_frame=%s focus_ok=%s ts=%s"
                  % (trip, w, v.get("window"), v.get("empty_window"), v.get("capture_ok"),
                     v.get("forensics_png"), v.get("current_frame"), v.get("focus_ok"), r.get("ts")))

print("\n########## 4. panel_p for ALL 27 end pngs (S543's own crop+criterion) ##########")
pngs = sorted(set(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png")) + glob.glob(os.path.join(BASE, "measure_w*_end_*.png"))))
hi = []
for p in pngs:
    im = Image.open(p).convert("RGB")
    a = np.asarray(im.crop((85, 108, 630, 275)))
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    pv = float(((b > r + 18) & (b > g + 10) & (b >= 40) & (b <= 190) & (r < 150)).sum()) / a[..., 0].size
    trip = os.path.basename(os.path.dirname(p))
    wn = os.path.basename(p).split("measure_w")[1].split("_")[0]
    jp = os.path.join(os.path.dirname(p), "measure_w%s.json" % wn)
    ed = (json.load(open(jp, encoding="utf-8")).get("frame_edges") or []) if os.path.exists(jp) else []
    df = (ed[-1][0] - ed[0][0]) if ed else None
    tag = "SCORE" if pv >= 0.30 else ("noPanel" if pv >= 0.02 else "nonGame")
    if pv >= 0.30:
        hi.append((trip, wn, pv))
    print("  %-20s w%s df=%-6s p=%.4f %-8s %s" % (trip, wn, df, pv, tag, os.path.relpath(p, BASE)))
print("  p>=0.30 count = %d / %d" % (len(hi), len(pngs)))
sub = [h for h in hi if h[0] != os.path.basename(BASE)]
print("  of which subdir-only = %d ; root-level = %d" % (len(sub), len(hi) - len(sub)))
