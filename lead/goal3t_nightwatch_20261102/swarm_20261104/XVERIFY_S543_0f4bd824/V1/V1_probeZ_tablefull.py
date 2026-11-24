"""V1 probe Z (v2): read the score table's numeric cells per player-coloured text.

Measured facts used (all from probes Q/N/R):
  - the table text is drawn in the PLAYER colour, e.g. l3 row1 = RGB(33,105,214),
    T40 row1 = RGB(255,24,24); the panel background is much darker.
  - data row 1 digit rows 196-209, data row 2 digit rows 233-246 (from probe K diff bands).
Method: pick the dominant colour with max-channel >= 200 in the row band -> mask |px-col|<50
-> column runs -> ink bbox -> match against the 5x9 / 4x9 digit templates read off
V1_probeH_out.txt (same engine font as the 时间 field).
"""
import os, glob
import numpy as np
from PIL import Image

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

T = {
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
LIB = {}
for k, v in T.items():
    LIB.setdefault((len(v), max(len(r) for r in v)), []).append(
        (k, np.array([[c == "#" for c in r.ljust(max(len(x) for x in v))] for r in v])))

ROWS = {"r1": (196, 210), "r2": (233, 247), "r3": (270, 284), "r4": (307, 321)}


def plate_ink(a):
    y = a[5:30, 665:760]
    r, g, b = y[:, :, 0].astype(int), y[:, :, 1].astype(int), y[:, :, 2].astype(int)
    return int(((r > 170) & (g > 150) & (b < 130)).sum())


def text_colour(a, y0, y1):
    band = a[y0:y1, 95:540].reshape(-1, 3)
    bright = band[band.max(axis=1) >= 200]
    if len(bright) == 0:
        return None, 0
    vals, cnt = np.unique(bright, axis=0, return_counts=True)
    i = int(np.argmax(cnt))
    return vals[i], int(cnt[i])


def runs_mask(a, colour, y0, y1, x0=95, x1=540, tol=60):
    sub = a[y0:y1, x0:x1].astype(int)
    d = np.abs(sub - colour).max(axis=2)
    return d < tol


def decode_runs(m, x0):
    cs = m.sum(axis=0)
    out, x = [], 0
    while x < m.shape[1]:
        if cs[x] > 0:
            y = x
            while y < m.shape[1] and cs[y] > 0:
                y += 1
            blk = m[:, x:y]
            ys, xs = np.where(blk)
            bb = blk[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            h, w = bb.shape
            cands = LIB.get((h, w), [])
            lab, err = "?", None
            if cands:
                sc = sorted(((int((bb != g).sum()), k) for k, g in cands))
                lab, err = sc[0][1], sc[0][0]
            out.append((x0 + x, x0 + y - 1, lab, err, h, w, int(bb.sum())))
            x = y
        else:
            x += 1
    return out


for f in sorted(glob.glob(ROOT + "/*/measure_w*_end_x.png")) + sorted(glob.glob(ROOT + "/measure_w*_end_x.png")):
    rel = f[len(ROOT) + 1:].replace("\\", "/")
    a = np.asarray(Image.open(f).convert("RGB"))
    pl = plate_ink(a)
    if pl < 200:
        print("%-46s plate=%3d -> NOT a score screen (no title plate ink)" % (rel, pl))
        continue
    line = ["%-44s plate=%3d" % (rel, pl)]
    for tag, (y0, y1) in ROWS.items():
        col, n = text_colour(a, y0, y1)
        if col is None:
            line.append("%s=-" % tag)
            continue
        runs = decode_runs(runs_mask(a, col, y0, y1), 95)
        digs = [(r[2], r[0], r[1]) for r in runs if r[4] == 9 and r[3] is not None and r[3] <= 6]
        s = "".join(d[0] for d in digs) if digs else "-"
        line.append("%s col%s(n%d) -> [%s] cells=%d" % (tag, tuple(int(v) for v in col), n, s, len(runs)))
    print("  " + "\n   ".join(line))
