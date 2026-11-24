"""V1 probe U: full window census across the whole qc161_u0400_trip tree.

For every measure_w*.json: n_edges, first/last frame, df, whether an _end_x.png shot exists,
and if it exists what my pixel criteria say (score screen / not). Answers the coverage
question: how many frozen windows exist, and how many are actually backed by a screenshot.
"""
import os, glob, json
import numpy as np
from PIL import Image

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"


def yellow(a):
    r = a[:, :, 0].astype(int); g = a[:, :, 1].astype(int); b = a[:, :, 2].astype(int)
    return (r > 170) & (g > 150) & (b < 130) & ((r - b) > 70) & ((g - b) > 50)


def ncells(m):
    sub = m[120:142, 480:545]
    cs = sub.sum(axis=0)
    n, x = 0, 0
    while x < cs.size:
        if cs[x] > 0:
            n += 1
            while x < cs.size and cs[x] > 0:
                x += 1
        else:
            x += 1
    return n


jfiles = sorted(glob.glob(ROOT + "/*/measure_w*.json")) + sorted(glob.glob(ROOT + "/measure_w*.json"))
print("measure_w*.json files: %d" % len(jfiles))
tot = {"win": 0, "frozen": 0, "frozen_shot": 0, "frozen_shot_score": 0, "frozen_noshot": 0,
       "advance": 0, "f0_0": 0, "back": 0, "slow": 0, "healthy": 0}
rows = []
for jf in jfiles:
    d = json.load(open(jf, encoding="utf-8"))
    fe = d.get("frame_edges") or []
    st = d.get("stats") or {}
    rel = jf[len(ROOT) + 1:].replace("\\", "/")
    trip = rel.split("/")[0] if "/" in rel else "(root)"
    png = jf.replace(".json", "_end_x.png")
    has = os.path.exists(png)
    f0 = fe[0][0] if fe else None
    f1 = fe[-1][0] if fe else None
    df = (f1 - f0) if fe else None
    kind = "no-edges"
    if fe:
        if df == 0 and f0 != 0:
            kind = "FROZEN"
            tot["frozen"] += 1
        elif f0 == 0 and df == 0:
            kind = "frozen@0"
            tot["f0_0"] += 1
        elif df < 0:
            kind = "BACKWARD"
            tot["back"] += 1
        else:
            kind = "advance"
            tot["advance"] += 1
            fa = st.get("fps_avg")
            if fa is not None:
                tot["slow" if fa < 28 else "healthy"] += 1
    shot = "-"
    if has:
        a = np.asarray(Image.open(png).convert("RGB"))
        m = yellow(a)
        shot = "SCORE" if (int(m[5:30, 665:760].sum()) > 200 and ncells(m) == 10) else "not-score"
    if kind == "FROZEN":
        if has:
            tot["frozen_shot"] += 1
            if shot == "SCORE":
                tot["frozen_shot_score"] += 1
        else:
            tot["frozen_noshot"] += 1
    tot["win"] += 1
    rows.append((rel, kind, f0, f1, df, len(fe), st.get("fps_avg"), has, shot))

print()
print("%-46s %-10s %-7s %-7s %-6s %-5s %-8s %-6s %s" % (
    "window", "kind", "f0", "f1", "df", "edge", "fps_avg", "shot", "shot-type"))
for r in rows:
    if r[1] == "FROZEN" or r[8] != "-":
        print("%-46s %-10s %-7s %-7s %-6s %-5s %-8s %-6s %s" % (
            r[0], r[1], r[2], r[3], r[4], r[5],
            ("%.2f" % r[6]) if isinstance(r[6], float) else r[6], r[7], r[8]))
print()
print("TOTALS:", json.dumps(tot, ensure_ascii=False))
print()
print("all windows by kind:")
from collections import Counter
print(Counter(r[1] for r in rows))
print()
print("windows with an _end_x.png shot: %d ; of them SCORE=%d" % (
    sum(1 for r in rows if r[7]), sum(1 for r in rows if r[8] == "SCORE")))
print("shots belonging to NON-frozen windows:")
for r in rows:
    if r[7] and r[1] != "FROZEN":
        print("   ", r)
