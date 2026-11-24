"""V1 probe R: read the score-table data rows by colour-isolating the player-coloured text,
then matching the 5x9 digit bitmaps against the SAME library used for the 时间 field.

Colours measured in probe Q: the table text is NOT yellow; row 1 of l3_20261023r is
RGB(33,105,214) (blue player colour), row 1 of archive_T33 is RGB(57,211,41) (green).
So: pick, per row band, the dominant colour that is far from the panel background, then
mask |px - colour| < 45.
"""
import os, glob
import numpy as np
from PIL import Image

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

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


def sig(pat):
    h, w = len(pat), max(len(p) for p in pat)
    c = np.zeros((h, w), dtype=bool)
    for r, row in enumerate(pat):
        for i, ch in enumerate(row):
            c[r, i] = ch == "#"
    return c


LIB = {k: sig(v) for k, v in GLYPHS.items()}


def match(bb):
    h, w = bb.shape
    best = []
    for lab, g in LIB.items():
        gh, gw = g.shape
        if (gh, gw) != (h, w):
            continue
        d = int((g ^ bb).sum())
        if d <= 4:
            best.append((d, lab))
    best.sort()
    return best


def read_row(path, y0, y1, x0=95, x1=545):
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    sub = a[y0:y1, x0:x1]
    flat = sub.reshape(-1, 3)
    vals, cnts = np.unique(flat, axis=0, return_counts=True)
    # candidate text colour = not the 3 most common (panel background), bright enough
    order = np.argsort(-cnts)
    bg = vals[order[:3]]
    cand = None
    for i in order:
        v = vals[i]
        if cnts[i] < 12:
            break
        if int(v.max()) < 150:
            continue
        if any(int(np.abs(v - b).max()) < 45 for b in bg):
            continue
        cand = v
        break
    if cand is None:
        return None, "no text colour found", []
    d = np.abs(sub - cand).max(axis=2)
    m = d < 45
    cs = m.sum(axis=0)
    out, x, cells = [], 0, []
    while x < m.shape[1]:
        if cs[x] > 0:
            y = x
            while y < m.shape[1] and cs[y] > 0:
                y += 1
            blk = m[:, x:y]
            ys, xs = np.where(blk)
            bb = blk[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            cells.append((x0 + x, x0 + y - 1, bb))
            x = y
        else:
            x += 1
    for i, (cx0, cx1, bb) in enumerate(cells):
        mm = match(bb)
        if len(mm) == 1:
            out.append((cx0, cx1, mm[0][1], "ok"))
        elif mm:
            out.append((cx0, cx1, mm[0][1], "tied" + str([x[1] for x in mm])))
        else:
            out.append((cx0, cx1, "?", "no-match %dx%d" % (bb.shape[1], bb.shape[0])))
    return cand, "%d cells" % len(cells), out


TARGETS = [r for r in ["l3_20261023r/measure_w2_end_x.png",
                       "archive_T33/measure_w1_end_x.png",
                       "archive_T34/measure_w1_end_x.png",
                       "archive_T36/measure_w1_end_x.png",
                       "archive_T38/measure_w2_end_x.png",
                       "archive_T40/measure_w1_end_x.png",
                       "archive_T41/measure_w1_end_x.png",
                       "archive_T43/measure_w1_end_x.png",
                       "archive_T44/measure_w1_end_x.png",
                       "archive_T45/measure_w1_end_x.png",
                       "archive_T49_u0800/measure_w1_end_x.png",
                       "archive_T39/measure_w2_end_x.png"] if True]

for rel in TARGETS:
    p = ROOT + "/" + rel
    print("=" * 78)
    print(rel)
    for (y0, y1, tag) in [(192, 212, "data row 1"), (231, 251, "data row 2"),
                          (270, 290, "data row 3"), (309, 329, "data row 4")]:
        cand, info, cells = read_row(p, y0, y1)
        txt = " ".join("%d-%d:%s%s" % (c[0], c[1], c[2], "" if c[3] == "ok" else "(" + c[3] + ")") for c in cells)
        print("  %-11s colour=%s %s" % (tag, cand, info))
        print("     %s" % txt)
