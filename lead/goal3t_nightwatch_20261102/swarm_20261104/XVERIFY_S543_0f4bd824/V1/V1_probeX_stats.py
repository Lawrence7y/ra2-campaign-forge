"""V1 probe X: statistics on the readings — quantisation-aware fps intervals, the 31.2
hypothesis test, common-rate intersection, band counts, and population coverage.
"""
import os, glob, json
import numpy as np
from PIL import Image

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
R0, R1, C0, C1 = 120, 142, 480, 545

GLYPHS = {
    "0": [".###.", "##.##", "##.##", "##.##", "##.##", "##.##", "##.##", "##.##", ".###."],
    "1": ["..##", ".###", "####", "#.##", "..##", "..##", "..##", "..##", "..##"],
    "2": [".###.", "##.##", "...##", "...##", "..##.", ".###.", "###..", "##...", "#####"],
    "3": [".###.", "##.##", "...##", "...##", "..##.", "...##", "...##", "##.##", ".###."],
    "4": ["..##.", "..##.", ".###.", ".###.", "#.##.", "#.##.", "#####", "..##.", "..##."],
    "5": [".####", ".##..", "##...", "####.", "#..##", "...##", "...##", "##.##", ".###."],
    "6": [".###.", "##.##", "##...", "####.", "##.##", "##.##", "##.##", "##.##", ".###."],
    "7": ["#####", "...##", "..##.", "..#..", ".##..", ".##..", ".##..", ".##..", ".##.."],
    "8": [".###.", "##.##", "##.##", "##.##", ".###.", "##.##", "##.##", "##.##", ".###."],
    "9": [".###.", "##.##", "##.##", "##.##", "##.##", ".####", "...##", "##.#.", ".###."],
}


def pad(pat):
    h, w = len(pat), max(len(p) for p in pat)
    c = np.array([[1 if pat[r][cc] == "#" else 0 for cc in range(w)] for r in range(h)], dtype=bool)
    o = np.zeros((8, 10), dtype=bool)
    o[:min(h, 8), :min(w, 10)] = c[:min(h, 8), :min(w, 10)]
    return "".join("1" if v else "0" for v in o.ravel())


SIG = {pad(v): k for k, v in GLYPHS.items()}
STALE = {"archive_T38/measure_w1_end_x.png": "byte-identical to archive_T36/measure_w1_end_x.png AND same mtime; "
                                             "qc151_fields.json says T38 w1 empty_window=false (no png written)"}


def yellow(a):
    r = a[:, :, 0].astype(int); g = a[:, :, 1].astype(int); b = a[:, :, 2].astype(int)
    return (r > 170) & (g > 150) & (b < 130) & ((r - b) > 70) & ((g - b) > 50)


def read(a):
    m = yellow(a)
    sub = m[R0:R1, C0:C1]
    cs = sub.sum(axis=0)
    cells, x = [], 0
    while x < sub.shape[1]:
        if cs[x] > 0:
            y = x
            while y < sub.shape[1] and cs[y] > 0:
                y += 1
            blk = sub[:, x:y]
            ys, xs = np.where(blk)
            bb = blk[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            h, w = bb.shape
            cv = np.zeros((8, 10), dtype=bool)
            cv[:min(h, 8), :min(w, 10)] = bb[:min(h, 8), :min(w, 10)]
            cells.append("".join("1" if v else "0" for v in cv.ravel()))
            x = y
        else:
            x += 1
    if len(cells) != 10:
        return None
    try:
        d = [SIG[cells[i]] for i in (2, 3, 5, 6, 8, 9)]
    except KeyError:
        return None
    return "%s%s:%s%s:%s%s" % tuple(d)


files = sorted(glob.glob(ROOT + "/*/measure_w*_end_x.png")) + sorted(glob.glob(ROOT + "/measure_w*_end_x.png"))
rows = []
for f in files:
    rel = f[len(ROOT) + 1:].replace("\\", "/")
    a = np.asarray(Image.open(f).convert("RGB"))
    t = read(a)
    jf = f.replace("_end_x.png", ".json")
    d = json.load(open(jf, encoding="utf-8"))
    fe = d.get("frame_edges") or []
    fr = (fe[-1][0] if fe else None)
    rec = dict(rel=rel, trip=rel.split("/")[0], w=int(rel.split("measure_w")[1][0]),
               time=t, f=fr, sec=None if t is None else int(t[:2]) * 3600 + int(t[3:5]) * 60 + int(t[6:]),
               stale=STALE.get(rel, ""))
    rows.append(rec)

print("=== feasible fps interval per shot (screen shows floor(elapsed), so fps in (f/(s+1), f/s]) ===")
print("%-46s %-10s %-7s %-10s %-20s %-8s %-8s" % ("shot", "time", "f", "sec", "feasible fps", "31.2?", "30.0?"))
for r in rows:
    if r["time"] is None or not r["f"]:
        print("%-46s %-10s %-7s %s" % (r["rel"], r["time"], r["f"], "no score-screen time field" + ("  [" + r["stale"] + "]" if r["stale"] else "")))
        continue
    lo, hi = r["f"] / (r["sec"] + 1), r["f"] / r["sec"]
    r["lo"], r["hi"] = lo, hi
    print("%-46s %-10s %-7d %-10d (%.2f, %.2f]     %-8s %-8s%s" % (
        r["rel"], r["time"], r["f"], r["sec"], lo, hi,
        "yes" if lo < 31.2 <= hi else "NO", "yes" if lo < 30.0 <= hi else "NO",
        "  [STALE COPY]" if r["stale"] else ""))

good = [r for r in rows if r.get("lo") and not r["stale"]]
print()
print("genuine score-screen shots with a readable time: %d" % len(good))
inband = [r for r in good if 29.9 <= r["f"] / r["sec"] <= 31.4]
print("implied fps (f/sec) inside the document's band 29.9..31.4 : %d/%d" % (len(inband), len(good)))
print("   outside:", [(r["rel"], round(r["f"] / r["sec"], 2)) for r in good if r not in inband])
lo_max = max(r["lo"] for r in good)
hi_min = min(r["hi"] for r in good)
print("common-rate feasibility: max lower bound %.2f, min upper bound %.2f -> %s" % (
    lo_max, hi_min, "NON-EMPTY " + str((round(lo_max, 2), round(hi_min, 2))) if lo_max < hi_min else "EMPTY (no single fps explains all rows)"))
g2 = [r for r in good if "l3_20261023r" not in r["rel"]]
print("excluding l3_20261023r: max lower %.2f  min upper %.2f -> %s" % (
    max(r["lo"] for r in g2), min(r["hi"] for r in g2),
    "non-empty" if max(r["lo"] for r in g2) < min(r["hi"] for r in g2) else "EMPTY"))
g3 = [r for r in g2 if "archive_T38" not in r["rel"]]
print("excluding l3 and T38 : max lower %.2f  min upper %.2f -> (%.2f, %.2f]" % (
    max(r["lo"] for r in g3), min(r["hi"] for r in g3), max(r["lo"] for r in g3), min(r["hi"] for r in g3)))
print("   31.2 inside that interval? ", max(r["lo"] for r in g3) < 31.2 <= min(r["hi"] for r in g3))
print("   30.0 inside that interval? ", max(r["lo"] for r in g3) < 30.0 <= min(r["hi"] for r in g3))
print()
print("=== per-trip best rate (f/sec) sorted ===")
for r in sorted(good, key=lambda x: x["f"] / x["sec"]):
    print("   %-40s f=%-6d sec=%-5d f/sec=%6.2f  feasible (%.2f, %.2f]" % (
        r["rel"], r["f"], r["sec"], r["f"] / r["sec"], r["lo"], r["hi"]))
