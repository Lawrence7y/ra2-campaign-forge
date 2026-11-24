"""Read-only probe #9 (mine):
(a) decompose the score-vs-nonscore and w1-vs-w2 differences into bands (tests the report's
    'left edge / top band 100% identical' claim, which my FULL/LEFTEDGE numbers contradicted);
(b) spot-check single pixel colours the report cites;
(c) verify S543 Sec 4-bis three-window frame table straight from qc151_fields.json.
"""
import os, json, glob
import numpy as np
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
def load(rel):
    return np.asarray(Image.open(os.path.join(ROOT, rel.replace("/", os.sep))).convert("RGB"), dtype=np.int16)

print("=== (a) band decomposition ===")
BANDS = {"top y0-100 x0-96": (0, 100, 0, 96), "left x0-96 y100-600": (100, 600, 0, 96),
         "full left col x0-96": (0, 600, 0, 96), "top band y0-100 all x": (0, 100, 0, 800),
         "bottom y500-600 all x": (500, 600, 0, 800), "art centre y100-600 x96-660": (100, 600, 96, 660),
         "sidebar x660-800": (0, 600, 660, 800)}
pairs = [("archive_T33/measure_w1_end_x.png", "archive_T33/measure_w2_end_x.png", "T33 score vs non-score"),
         ("archive_T45/measure_w1_end_x.png", "archive_T45/measure_w2_end_x.png", "T45 score vs non-score"),
         ("archive_T34/measure_w1_end_x.png", "archive_T34/measure_w2_end_x.png", "T34 w1 vs w2"),
         ("archive_T44/measure_w1_end_x.png", "archive_T44/measure_w2_end_x.png", "T44 w1 vs w2"),
         ("measure_w1_end_x.png", "measure_w2_end_x.png", "root T55h w1 vs w2")]
for p1, p2, tag in pairs:
    a1, a2 = load(p1), load(p2)
    print(f"-- {tag}")
    for name, (r0, r1, c0, c1) in BANDS.items():
        d = np.abs(a1[r0:r1, c0:c1] - a2[r0:r1, c0:c1])
        n = int((d.max(2) > 0).sum())
        tot = (r1 - r0) * (c1 - c0)
        print(f"   {name:26s} diffpix={n:7d}/{tot:7d} ({100*(1-n/tot):6.2f}% identical) max={int(d.max())}")

print("\n=== (b) single-pixel spot checks (row,col) ===")
t34w1, t34w2 = load("archive_T34/measure_w1_end_x.png"), load("archive_T34/measure_w2_end_x.png")
for (r, c) in [(88, 719), (246, 164), (130, 490), (200, 355)]:
    print(f"   ({r},{c}) w1={tuple(int(x) for x in t34w1[r, c])} w2={tuple(int(x) for x in t34w2[r, c])}")

print("\n=== (c) S543 Sec 4-bis: frames per window from qc151_fields.json ===")
want = {"archive_T34": "QC161-U0400-T34", "archive_T36": "QC161-U0400-T36",
        "archive_T43": "QC161-U0400-T43", "archive_T40": "QC161-U0400-T40",
        "l3_1101v4d": None, "l3_1101v4e": None, "l3_20261023q": None,
        "t55k_20261020": None, "l1_20261020": None}
for td in want:
    fp = os.path.join(ROOT, td, "qc151_fields.json")
    if not os.path.exists(fp):
        cands = [p for p in glob.glob(os.path.join(ROOT, "*", "qc151_fields.json")) if td.lower() in os.path.basename(os.path.dirname(p)).lower()]
        print(f"   dir '{td}' not found; similar dirs: {[os.path.basename(os.path.dirname(x)) for x in cands][:6]}")
        continue
    tab = {}
    for e in json.load(open(fp, encoding="utf-8")):
        if e.get("group") == "MEASURE" and str(e.get("key", "")).startswith("measure_forensics_w"):
            v = e["value"]
            tab[v.get("window")] = (v.get("current_frame"), v.get("empty_window"), v.get("focus_ok"), bool(v.get("forensics_png")))
    print(f"   {td}: " + "  ".join(f"w{w}={tab.get(w)}" for w in (0, 1, 2)))
