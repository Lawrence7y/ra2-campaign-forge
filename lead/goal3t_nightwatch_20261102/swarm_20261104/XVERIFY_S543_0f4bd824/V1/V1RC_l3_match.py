"""Read-only probe #7d (mine): segment + classify the l3 score-table body digits.
Templates are the 9 glyph shapes I read off the yellow timer (V1RC_cells2_out.txt), so the
font mapping is one single self-consistent reading, not a per-field guess."""
import os, hashlib
import numpy as np
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
TEMPL = {
 "0": [".###.", "##.##", "##.##", "##.##", "##.##", "##.##", "##.##", "##.##", ".###."],
 "1": ["..##", ".###", "####", "#.##", "..##", "..##", "..##", "..##", "..##"],
 "2": [".###.", "##.##", "...##", "...##", "..##.", ".###.", "###..", "##...", "#####"],
 "3": [".###.", "##.##", "...##", "...##", "..##.", "...##", "...##", "##.##", ".###."],
 "4": ["..##.", "..##.", ".###.", ".###.", "#.##.", "#.##.", "#####", "..##.", "..##."],
 "5": [".####", ".##..", "##...", "####.", "#..##", "...##", "...##", "##.##", ".###."],
 "6": [".###.", "##.##", "##...", "####.", "##.##", "##.##", "##.##", "##.##", ".###."],
 "8": [".###.", "##.##", "##.##", "##.##", ".###.", "##.##", "##.##", "##.##", ".###."],
 "9": [".###.", "##.##", "##.##", "##.##", "##.##", ".####", "...##", "##.#.", ".###."],
}
# 7 and a few others never occurred in the timer; add them ONLY as candidate distractors,
# flagged as 'template not verified by any timer glyph'
UNVERIFIED = {
 "7": ["#####", "....#", "...#.", "..#..", "..#..", ".#...", ".#...", "#....", "#...."],
}
PAD = {}
for k, v in list(TEMPL.items()) + list(UNVERIFIED.items()):
    rows = [(r + "." * 5)[:5] for r in v]
    PAD[k] = np.array([[c == "#" for c in r] for r in rows], dtype=bool)

a = np.asarray(Image.open(os.path.join(ROOT, "l3_20261023r", "measure_w2_end_x.png")).convert("RGB"), dtype=np.int16)

def cells_in_band(r0, r1, c0, c1, ref, tol=90):
    reg = a[r0:r1 + 1, c0:c1 + 1]
    m = (np.abs(reg - np.array(ref)).sum(2) < tol)
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
        ink = int(sub.sum())
        if ink < 12:
            continue
        rows = np.where(sub.any(1))[0]
        sub = sub[rows.min():rows.max() + 1]
        out.append((c0 + x0, c0 + x1, ink, sub))
    return out

def classify(sub):
    h, w = sub.shape
    best = []
    for k, t in PAD.items():
        th, tw = t.shape
        if abs(h - th) > 1 or w > tw + 2:
            continue
        # align top-left, pad sub to th x tw
        canvas = np.zeros((th, tw), dtype=bool)
        canvas[:min(h, th), :min(w, tw)] = sub[:min(h, th), :min(w, tw)]
        inter = int((canvas & t).sum()); union = int((canvas | t).sum())
        best.append((inter / union if union else 0, k, h, w))
    best.sort(reverse=True)
    return best

for tag, (r0, r1, ref) in {"row1(blue)": (190, 215, (33, 105, 214)), "row2(red)": (228, 255, (255, 24, 24))}.items():
    print(f"===== {tag} =====")
    seq = []
    for (x0, x1, ink, sub) in cells_in_band(r0, r1, 90, 575, ref):
        b = classify(sub)
        top = b[0] if b else (0, "?", 0, 0)
        second = b[1] if len(b) > 1 else (0, "?", 0, 0)
        txt = "/".join("".join("#" if v else "." for v in r) for r in sub)
        print(f" cell cols{x0}-{x1} ink={ink} h={sub.shape[0]} w={sub.shape[1]} "
              f"best='{top[1]}' IoU={top[0]:.3f} 2nd='{second[1]}' IoU={second[0]:.3f} "
              f"sha={hashlib.sha256(txt.encode()).hexdigest()[:10]}")
        for r in txt.split("/"):
            print("     " + r)
        seq.append(top[1])
    print("  sequence of best matches:", "".join(str(s) for s in seq))
