"""Read-only probes #5+#6 (mine):
(a) window-level census over EVERY measure_w*.json in the trip tree (sample-vs-population check);
(b) the 31.2 / quantisation test, computed on MY OWN readings.
"""
import os, json, glob, math
import numpy as np

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

# ---------- (a) census ----------
jfiles = sorted(glob.glob(os.path.join(ROOT, "**", "measure_w*.json"), recursive=True))
print("n measure_w*.json (recursive):", len(jfiles))
rows = []
for p in jfiles:
    d = json.load(open(p, encoding="utf-8"))
    fe = d.get("frame_edges") or []
    png = p[:-5] + "_end_x.png"
    rel = os.path.relpath(p, ROOT).replace("\\", "/")
    f0 = fe[0][0] if fe else None
    f1 = fe[-1][0] if fe else None
    cls = ("no-edges" if not fe else
           "BACKWARD" if f1 < f0 else
           "frozen@0" if (f1 == f0 and f0 == 0) else
           "FROZEN" if f1 == f0 else "advance")
    st = d.get("stats") or {}
    rows.append(dict(rel=rel, trip=d.get("trip_id"), win=d.get("window"), cls=cls, f0=f0, f1=f1,
                     ne=len(fe), df=(f1 - f0) if fe else None,
                     fps_avg=st.get("fps_avg"), png=os.path.exists(png)))
from collections import Counter
c = Counter(r["cls"] for r in rows)
print("class counts:", dict(c))
frz = [r for r in rows if r["cls"] == "FROZEN"]
print("FROZEN windows:", len(frz))
print("  with png:", sum(1 for r in frz if r["png"]), " without:", sum(1 for r in frz if not r["png"]))
print("  no-png list:", [(r["trip"], r["win"], r["f0"]) for r in frz if not r["png"]])
adv = [r for r in rows if r["cls"] == "advance"]
print("advance:", len(adv), " fps_avg>=28:", sum(1 for r in adv if (r["fps_avg"] or 0) >= 28),
      " <28:", sum(1 for r in adv if (r["fps_avg"] or 0) < 28))
print("trips (distinct trip_id):", len({r["trip"] for r in rows}))

# which frozen windows have a png, and does that png show the score layout?
SCORE = set()   # my own layout test, recomputed here
def is_score(path):
    from PIL import Image
    a = np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)
    m = (a[..., 0] > 200) & (a[..., 1] > 200) & (a[..., 2] < 110) & ((a[..., 0] - a[..., 2]) > 60)
    return int(m[9:24, 400:800].sum()), int(m[160:175, 99:529].sum())
for r in frz:
    pngp = os.path.join(ROOT, r["rel"].replace(".json", "_end_x.png").replace("/", os.sep))
    if r["png"]:
        t, h = is_score(pngp)
        r["titleInk"], r["hdrInk"], r["score"] = t, h, (t == 361 and h == 993)
print("  FROZEN w/ png & score layout:", sum(1 for r in frz if r.get("score")))
print("  FROZEN w/ png & NOT score     :", [(r["trip"], r["win"]) for r in frz if r["png"] and not r.get("score")])
png_all = [r for r in rows if r["png"]]
print("windows (any class) with an end png:", len(png_all),
      " of them advance:", [(r["trip"], r["win"], r["df"]) for r in png_all if r["cls"] == "advance"])
print("frozen@0 windows:", [(r["trip"], r["win"], r["png"]) for r in rows if r["cls"] == "frozen@0"])

# ---------- (b) 31.2 test on my own readings ----------
# (trip, f1, secs) from V1RC_consolidated_out.txt readings; T38 uses w2 (its w1 is T36's copy)
READS = [("T55h<root>", 373, 13), ("T33", 738, 24), ("T34", 302, 10), ("T36", 310, 10),
         ("T38w2", 940, 32), ("T39", 945, 31), ("T40", 908, 30), ("T41", 860, 28),
         ("T43", 314, 10), ("T44", 883, 29), ("T45", 845, 28), ("T49", 448, 15),
         ("l3_20261023r", 4367, 176)]
print("\n(b) quantisation feasibility, my own readings")
for model in ("floor", "round"):
    for r_ in (31.2, 30.0):
        ok = [(n) for (n, f, s) in READS if (math.floor(f / r_) == s if model == "floor" else abs(f / r_ - s) <= 0.5)]
        print(f"  {model} rate={r_}: feasible rows {len(ok)}/{len(READS)} -> {ok}")
    lo = max(f / (s + 1) for (n, f, s) in READS if n != "l3_20261023r" and n != "T38w2")
    hi = min(f / s for (n, f, s) in READS if n != "l3_20261023r" and n != "T38w2")
    print(f"  {model}: common rate interval over the 11 short trips = ({lo:.4f}, {hi:.4f}]  "
          f"contains 31.2? {lo < 31.2 <= hi}  contains 30.0? {lo < 30.0 <= hi}")
for n, f, s in READS:
    print(f"   {n:14s} f={f:5d} s={s:4d} floor-interval=({f/(s+1):.4f}, {f/s:.4f}] round-interval=[{f/(s+0.5):.4f}, {f/(s-0.5):.4f}]")
