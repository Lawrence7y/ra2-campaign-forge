"""Read-only probe #12 (mine): digit-level read of the score-table body on three short trips,
using the same self-built font as the timer. Reference (text) colour is chosen automatically
from the band's colour census; the winning colour is the one that maximises exact template hits."""
import os, glob, json
from collections import Counter
import numpy as np
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
TEMPL = {
 "0": [".###.", "##.##", "##.##", "##.##", "##.##", "##.##", "##.##", "##.##", ".###."],
 "1": ["..##.", ".###.", "####.", "#.##.", "..##.", "..##.", "..##.", "..##.", "..##."],
 "2": [".###.", "##.##", "...##", "...##", "..##.", ".###.", "###..", "##...", "#####"],
 "3": [".###.", "##.##", "...##", "...##", "..##.", "...##", "...##", "##.##", ".###."],
 "4": ["..##.", "..##.", ".###.", ".###.", "#.##.", "#.##.", "#####", "..##.", "..##."],
 "5": [".####", ".##..", "##...", "####.", "#..##", "...##", "...##", "##.##", ".###."],
 "6": [".###.", "##.##", "##...", "####.", "##.##", "##.##", "##.##", "##.##", ".###."],
 "7": ["#####", "....#", "...#.", "..#..", "..#..", ".#...", ".#...", ".#...", ".#..."],
 "8": [".###.", "##.##", "##.##", "##.##", ".###.", "##.##", "##.##", "##.##", ".###."],
 "9": [".###.", "##.##", "##.##", "##.##", "##.##", ".####", "...##", "##.#.", ".###."],
}
T = {k: np.array([[c == "#" for c in r] for r in v]) for k, v in TEMPL.items()}

def cells_for(a, r0, r1, ref, tol=90):
    reg = a[r0:r1 + 1, 90:575]
    m = np.abs(reg - np.array(ref)).sum(2) < tol
    cols = m.any(0)
    runs, x = [], 0
    while x < len(cols):
        if cols[x]:
            y = x
            while y + 1 < len(cols) and cols[y + 1]:
                y += 1
            runs.append((x, y)); x = y + 1
        else:
            x += 1
    out = []
    for (x0, x1) in runs:
        sub = m[:, x0:x1 + 1]
        if int(sub.sum()) < 12 or (x1 - x0 + 1) > 5:
            continue
        rows = np.where(sub.any(1))[0]
        if rows.max() - rows.min() + 1 != 9:
            continue
        sub = sub[rows.min():rows.min() + 9]
        canvas = np.zeros((9, 5), dtype=bool)
        canvas[:, 5 - sub.shape[1]:] = sub          # right-align narrow glyphs (the '1')
        best = max(((int((canvas & t).sum()) / int((canvas | t).sum()), k) for k, t in T.items()))
        out.append((90 + x0, 90 + x1, best[1], best[0]))
    return out

def sat_colours(a, r0, r1):
    reg = a[r0:r1 + 1, 250:570].astype(np.uint8)
    mx, mn = reg.max(2), reg.min(2)
    sel = reg[((mx - mn) > 60) & (mx > 120)]
    return [tuple(int(x) for x in c) for c, _ in Counter(map(tuple, sel)).most_common(6)]

for rel in ["archive_T40/measure_w1_end_x.png", "archive_T33/measure_w1_end_x.png",
            "archive_T49_u0800/measure_w2_end_x.png", "archive_T38/measure_w2_end_x.png",
            "l3_20261023r/measure_w2_end_x.png"]:
    a = np.asarray(Image.open(os.path.join(ROOT, rel.replace("/", os.sep))).convert("RGB"), dtype=np.int16)
    print(f"### {rel}")
    for (r0, r1, tag) in ((194, 216, "row1"), (230, 252, "row2")):
        best = None
        for ref in sat_colours(a, r0, r1):
            cs = cells_for(a, r0, r1, ref)
            score = sum(1 for c in cs if c[3] == 1.0)
            if best is None or score > best[0]:
                best = (score, ref, cs)
        score, ref, cs = best
        print(f"  {tag}: best text colour {ref}, exact-glyph cells={score}")
        print("      cells:", [(c[0], c[2], round(c[3], 3)) for c in cs])
        print("      reading:", "".join(c[2] for c in cs))
