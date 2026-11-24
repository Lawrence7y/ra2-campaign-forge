"""V1 probe W: decode the score-table body of every score-screen shot.

Geometry measured in probes N/R/T:
  four right-aligned numeric columns, right edges 286 / 369 / 451 / 528 (px), digit cell
  5 px wide with 6 px pitch, digit rows 199-207 (data row 1) and 236-244 (data row 2).
Ink predicate: pixel max-channel > (45th-percentile of the cell window + 35)  -- i.e. text
stands out of the local background; the same rule that produced legible bitmaps in probe T.
Digits are matched against the 5x9 template library (shapes read off printed bitmaps in
V1_probeH_out.txt). Also hashes the whole table body so identical bodies group together.
"""
import os, glob, hashlib
import numpy as np
from PIL import Image

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

GLYPHS = {
    "0": [".###.", "##.##", "##.##", "##.##", "##.##", "##.##", "##.##", "##.##", ".###."],
    "1": ["..##.", "..##.", ".###.", ".###.", "#.##.", "#.##.", "#####", "..##.", "..##."],
    "2": [".###.", "##.##", "...##", "...##", "..##.", ".###.", "###..", "##...", "#####"],
    "3": [".###.", "##.##", "...##", "...##", "..##.", "...##", "...##", "##.##", ".###."],
    "4": ["..##.", "..##.", ".###.", ".###.", "#.##.", "#.##.", "#####", "..##.", "..##."],
    "5": [".####", ".##..", "##...", "####.", "#..##", "...##", "...##", "##.##", ".###."],
    "6": [".###.", "##.##", "##...", "####.", "##.##", "##.##", "##.##", "##.##", ".###."],
    "7": ["#####", "...##", "..##.", "..#..", ".##..", ".##..", ".##..", ".##..", ".##.."],
    "8": [".###.", "##.##", "##.##", "##.##", ".###.", "##.##", "##.##", "##.##", ".###."],
    "9": [".###.", "##.##", "##.##", "##.##", "##.##", ".####", "...##", "##.#.", ".###."],
}
# 1 and 4 differ; keep both.  Build boolean arrays.
def arr(pat):
    return np.array([[c == "#" for c in row] for row in pat], dtype=bool)
LIB = {k: arr(v) for k, v in GLYPHS.items()}
for k, v in LIB.items():
    assert v.shape == (9, 5), (k, v.shape)


def cell_ink(a, x0, y0, w=5, h=9):
    win = a[y0 - 1:y0 + h + 1, x0 - 1:x0 + w + 1].astype(int)
    mx = win.max(axis=2)
    thr = np.percentile(mx, 45) + 35
    m = mx > thr
    return m[1:1 + h, 1:1 + w]


def decode(a, right_edge, y0, ndigit):
    out = []
    for i in range(ndigit):
        x0 = right_edge - 5 - 6 * (ndigit - 1 - i)
        m = cell_ink(a, x0, y0)
        frac = float(m.mean())
        if frac < 0.10:
            out.append((".", 0.0))
            continue
        best = sorted(((int(m ^ g).sum(), lab) for lab, g in LIB.items()))
        out.append((best[0][1], best[0][0]))
    return out


SHOTS = sorted(glob.glob(ROOT + "/*/measure_w*_end_x.png")) + sorted(glob.glob(ROOT + "/measure_w*_end_x.png"))
COLS = [(286, "c1"), (369, "c2"), (451, "c3"), (528, "c4")]
print("%-46s %-6s %-22s %-22s %s" % ("shot", "y0", "row1 (c1 c2 c3 c4)", "row2", "table-body sha8"))
for p in SHOTS:
    rel = p[len(ROOT) + 1:].replace("\\", "/")
    a = np.asarray(Image.open(p).convert("RGB"))
    if int((a[5:30, 665:760][:, :, 0].astype(int) > 170).sum()) < 100:
        print("%-46s NOT A SCORE SCREEN (no title plate)" % rel)
        continue
    body = a[188:260, 95:540]
    sh = hashlib.sha256(body.tobytes()).hexdigest()[:8]
    for y0 in (198, 199, 200):
        r = []
        for ce, name in COLS:
            r.append("".join(d for d, _ in decode(a, ce, y0, 4)))
        cells_nonempty = sum(1 for x in r if x.strip("."))
        if cells_nonempty >= 3:
            break
    row1 = []
    for ce, name in COLS:
        digs = decode(a, ce, y0, 4)
        s = "".join(d for d, _ in digs).lstrip(".") or "-"
        err = max([e for _, e in digs if e > 0] or [0])
        row1.append("%s=%s(e%d)" % (name, s, err))
    row2 = []
    for ce, name in COLS:
        digs = decode(a, ce, y0 + 37, 4)
        s = "".join(d for d, _ in digs).lstrip(".") or "-"
        err = max([e for _, e in digs if e > 0] or [0])
        row2.append("%s=%s(e%d)" % (name, s, err))
    print("%-46s y0=%-4d %-58s %-58s %s" % (rel, y0, " ".join(row1), " ".join(row2), sh))
