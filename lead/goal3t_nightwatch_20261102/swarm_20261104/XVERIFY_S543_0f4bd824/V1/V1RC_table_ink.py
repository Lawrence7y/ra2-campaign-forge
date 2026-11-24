"""Read-only probe #11 (mine): how full is the score-table body on each score screen?
Tests 'the other trips' rows are placeholders' without reading individual digits:
counts 5x9-shaped ink cells per row band, using a colour-agnostic ink mask."""
import os
import numpy as np
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
import glob
files = sorted(glob.glob(os.path.join(ROOT, "**", "measure_w*_end_x.png"), recursive=True))
print(f"{'png':44s} {'body_rows_194-216':>18s} {'body_rows_230-252':>18s}  cells r1  cells r2")
for p in files:
    a = np.asarray(Image.open(p).convert("RGB"), dtype=np.int16)
    out = []
    for (r0, r1) in ((194, 216), (230, 252)):
        reg = a[r0:r1 + 1, 95:570]
        # ink = saturated & bright compared with the dark panel behind the table
        mx, mn = reg.max(2), reg.min(2)
        lum = reg.mean(2)
        ink = ((mx - mn) > 60) & (mx > 120)
        cols = ink.any(0)
        runs, x, cells = [], 0, 0
        while x < len(cols):
            if cols[x]:
                y = x
                while y + 1 < len(cols) and cols[y + 1]:
                    y += 1
                if int(ink[:, x:y + 1].sum()) >= 12 and (y - x) <= 7:
                    cells += 1
                x = y + 1
            else:
                x += 1
        out.append((int(ink.sum()), cells))
    rel = os.path.relpath(p, ROOT).replace("\\", "/")
    print(f"{rel:44s} {out[0][0]:18d} {out[1][0]:18d}  {out[0][1]:7d}  {out[1][1]:7d}")
