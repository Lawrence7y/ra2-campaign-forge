"""Final numbers for the recheck report:
 (P) slow-window (fps<28) independence: dirs and map_sha256 concentration  (V2 §2 claims 16+13 of 38)
 (Q) FRZ windows: own png present? table present? — with a correct png-path test
 (R) v4-b wait trace: does the frame counter advance there at all?

Run: python -I -X utf8 v2r_counts.py
"""
import os, glob, json, re, statistics
from collections import Counter, defaultdict
import numpy as np
from PIL import Image

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
SUB = sorted(glob.glob(os.path.join(R, "*", "measure_w*.json")))
ROOT = sorted(glob.glob(os.path.join(R, "measure_w*.json")))

Y0, Y1 = 124, 138
SLOTS = [(488, 492), (494, 498), (503, 507), (509, 513), (518, 522), (524, 528)]
COLONS = [(485, 486), (500, 501), (515, 516)]


def cls(d):
    fe = d.get("frame_edges") or []
    if not fe:
        return "NO_EDGES", None, None
    f0, f1 = fe[0][0], fe[-1][0]
    df = f1 - f0
    return ("ADV" if df > 0 else ("LOAD" if f0 == 0 and df == 0 else ("FRZ" if df == 0 else "BACK"))), f0, df


rows = []
for p in SUB + ROOT:
    d = json.load(open(p, encoding="utf-8"))
    rel = os.path.relpath(p, R).replace("\\", "/")
    dr = "." if p in ROOT else rel.split("/")[0]
    k, f0, df = cls(d)
    rows.append(dict(rel=rel, dir=dr, k=k, f0=f0, df=df, d=d, map=(d.get("map_sha256") or "")[:8],
                     fps=(d.get("stats") or {}).get("fps_avg")))

slow = [r for r in rows if r["k"] == "ADV" and (r["fps"] or 0) < 28]
fast = [r for r in rows if r["k"] == "ADV" and (r["fps"] or 0) >= 28]
print(f"[P] slow windows n={len(slow)} dirs={len({r['dir'] for r in slow})} ; fast n={len(fast)}")
mc = Counter(r["map"] for r in slow)
print("    map_sha256 concentration among the 38 slow windows:", mc.most_common())
print("    top-2 maps cover:", sum(n for _, n in mc.most_common(2)), "of", len(slow))
print("    per-map for the 25 fast windows:", Counter(r['map'] for r in fast).most_common())
dc = Counter(r["dir"] for r in slow)
print("    dirs contributing 3 slow windows:", [d for d, n in dc.items() if n == 3])

print("\n[Q] FRZ windows: own end png, and does that png carry the HH:MM:SS field?")
frz = [r for r in rows if r["k"] == "FRZ"]
tab = nopng = nopic = 0
for r in sorted(frz, key=lambda x: x["rel"]):
    m = re.match(r"^(.*)/measure_w(\d+)\.json$", r["rel"])
    if m:
        png = os.path.join(R, m.group(1), f"measure_w{m.group(2)}_end_x.png")
    else:
        png = os.path.join(R, re.match(r"^measure_w(\d+)\.json$", r["rel"]).group(0).replace(".json", "_end_x.png"))
    if not os.path.exists(png):
        nopng += 1
        print(f"    {r['rel']:38s} NO PNG")
        continue
    arr = np.asarray(Image.open(png).convert("RGB")).astype(np.int16)
    ym = (arr[:, :, 0] > 150) & (arr[:, :, 1] > 120) & (arr[:, :, 2] < 110)
    ok = all(ym[Y0:Y1 + 1, a:b + 1].sum() > 0 for a, b in SLOTS) and all(ym[Y0:Y1 + 1, a:b + 1].sum() > 0 for a, b in COLONS)
    if ok:
        tab += 1
    else:
        nopic += 1
    print(f"    {r['rel']:38s} f0={r['f0']:6d} png=yes table={'YES' if ok else 'no '}")
print(f"    FRZ windows={len(frz)} with score table visible={tab} png-but-no-table={nopic} no-png={nopng}")
sub = [r for r in frz if r["dir"] != "."]
print(f"    restricted to the 29 subdir FRZ: windows={len(sub)}")

print("\n[R] l3_1101v4b wait trace: frame counter advance in the OTHER channel")
for dr in ["l3_1101v4b", "l3_1101v4e"]:
    p = os.path.join(R, dr, "h8_wait_trace.json")
    d = json.load(open(p, encoding="utf-8"))
    sm = d["samples"]
    fs = [x[1] for x in sm]
    ts = [x[0] for x in sm]
    rises = sum(1 for i in range(1, len(fs)) if fs[i] > fs[i - 1])
    print(f"    {dr}: verdict={d['verdict']} wait_s={d['wait_s']} samples={len(sm)} "
          f"f 0->{max(fs)} rising_edges={rises} mean_advance={(max(fs)-min(fs))/ts[-1]:.3f} frame/s")
