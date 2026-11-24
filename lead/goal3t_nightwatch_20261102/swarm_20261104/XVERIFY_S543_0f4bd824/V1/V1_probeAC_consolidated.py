"""V1 probe AC: one consolidated table for REPORT.md (27 shots x all measured columns)."""
import os, glob, json, hashlib
import numpy as np
from PIL import Image

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
GL = {
    "0": ".###. ##.## ##.## ##.## ##.## ##.## ##.## ##.## .###.".split(),
    "1": "..## .### #### #.## ..## ..## ..## ..## ..##".split(),
    "2": ".###. ##.## ...## ...## ..##. .###. ###.. ##... #####".split(),
    "3": ".###. ##.## ...## ...## ..##. ...## ...## ##.## .###.".split(),
    "4": "..##. ..##. .###. .###. #.##. #.##. ##### ..##. ..##.".split(),
    "5": ".#### .##.. ##... ####. #..## ...## ...## ##.## .###.".split(),
    "6": ".###. ##.## ##... ####. ##.## ##.## ##.## ##.## .###.".split(),
    "7": "##### ...## ..##. ..#.. .##.. .##.. .##.. .##.. .##..".split(),
    "8": ".###. ##.## ##.## ##.## .###. ##.## ##.## ##.## .###.".split(),
    "9": ".###. ##.## ##.## ##.## ##.## .#### ...## ##.#. .###.".split(),
}


def psig(pat):
    h, w = len(pat), max(len(p) for p in pat)
    c = np.array([[(ch == "#") for ch in p.ljust(w)] for p in pat])
    o = np.zeros((8, 10), dtype=bool)
    o[:min(h, 8), :min(w, 10)] = c[:min(h, 8), :min(w, 10)]
    return "".join("1" if v else "0" for v in o.ravel())


SIG = {}
for k, v in GL.items():
    SIG.setdefault(psig(v), []).append(k)


def ym(a):
    r, g, b = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
    return (r > 170) & (g > 150) & (b < 130) & ((r - b) > 70) & ((g - b) > 50)


def cellsig(m):
    sub = m[120:142, 480:545]
    cs = sub.sum(axis=0)
    out, x = [], 0
    while x < cs.size:
        if cs[x] > 0:
            y = x
            while y < cs.size and cs[y] > 0:
                y += 1
            blk = sub[:, x:y]
            ys, xs = np.where(blk)
            bb = blk[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            h, w = bb.shape
            o = np.zeros((8, 10), dtype=bool)
            o[:min(h, 8), :min(w, 10)] = bb[:min(h, 8), :min(w, 10)]
            out.append("".join("1" if v else "0" for v in o.ravel()))
            x = y
        else:
            x += 1
    return out


rows = []
for f in sorted(glob.glob(ROOT + "/*/measure_w*_end_x.png")) + sorted(glob.glob(ROOT + "/measure_w*_end_x.png")):
    rel = f[len(ROOT) + 1:].replace("\\", "/")
    a = np.asarray(Image.open(f).convert("RGB"))
    m = ym(a)
    cl = cellsig(m)
    t = "-"
    if len(cl) == 10:
        try:
            d = [SIG[cl[i]][0] for i in (2, 3, 5, 6, 8, 9)]
            t = "%s%s:%s%s:%s%s" % tuple(d)
        except Exception:
            t = "?"
    sec = None
    if t.count(":") == 2:
        hh, mm, ss = t.split(":")
        sec = int(hh) * 3600 + int(mm) * 60 + int(ss)
    jf = f.replace("_end_x.png", ".json")
    d = json.load(open(jf, encoding="utf-8"))
    fe = d.get("frame_edges") or []
    fr = fe[-1][0] if fe else None
    st = os.stat(f)
    rows.append(dict(rel=rel, plate=int(m[5:30, 665:760].sum()),
                     colh=int(m[160:175, 99:529].sum()), ncell=len(cl), time=t, sec=sec,
                     f=fr, nedge=len(fe),
                     ratio=(fr / sec) if (sec and fr) else None,
                     pixsha=hashlib.sha256(a.tobytes()).hexdigest()[:10],
                     mtime=int(st.st_mtime), win_end=d["t_abs0"] + d["span_s"],
                     trip=d.get("trip_id")))

print("| # | 图 | 类 | plate | 表头ink | cells | 屏显时间 | 秒 | json末帧 | n_edges | 帧/秒 | pixsha前10 | mtime-窗末 | trip_id |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
groups = {}
for r in rows:
    groups.setdefault(r["pixsha"], []).append(r["rel"])
dupmark = {}
for h, v in groups.items():
    if len(v) > 1:
        for x in v:
            dupmark[x] = len(v)
for i, r in enumerate(rows):
    cls = "SCORE" if (r["plate"] == 361 and r["ncell"] == 10) else "not-score"
    print("| %d | %s | %s | %d | %d | %d | %s | %s | %s | %d | %s | %s | %+.1f%s | %s |" % (
        i, r["rel"], cls, r["plate"], r["colh"], r["ncell"], r["time"],
        r["sec"] if r["sec"] is not None else "-", r["f"], r["nedge"],
        ("%.2f" % r["ratio"]) if r["ratio"] else "-", r["pixsha"],
        r["mtime"] - r["win_end"], (" DUPx%d" % dupmark[r["rel"]]) if r["rel"] in dupmark else "",
        r["trip"]))

print()
print("score screens: %d / %d" % (sum(1 for r in rows if r["plate"] == 361 and r["ncell"] == 10), len(rows)))
print("dup groups (pixsha):")
for h, v in groups.items():
    if len(v) > 1:
        print("   %s : %s" % (h, v))
print("distinct pixsha: %d of %d ; among the 25 under trip dirs: %d" % (
    len(groups), len(rows),
    len({r["pixsha"] for r in rows if "/" in r["rel"]})))
ratios = sorted([r["ratio"] for r in rows if r["ratio"] and r["rel"] != "archive_T38/measure_w1_end_x.png"])
print()
print("ratio f/sec over all genuine score shots (T38/w1 excluded as stale copy): n=%d min=%.2f max=%.2f" % (
    len(ratios), min(ratios), max(ratios)))
print("in [29.9,31.4]: %d ; outside: %s" % (
    sum(1 for x in ratios if 29.9 <= x <= 31.4), [round(x, 2) for x in ratios if not (29.9 <= x <= 31.4)]))
