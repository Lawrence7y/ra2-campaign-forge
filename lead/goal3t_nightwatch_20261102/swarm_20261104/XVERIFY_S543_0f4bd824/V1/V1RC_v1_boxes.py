"""Read-only probe #10 (mine): recompute V1's own region boxes verbatim, in my code, to see
whether the percentages in its REPORT are reproducible or a transcription slip."""
import os
import numpy as np
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
REGIONS = {
    "far-left edge x0-95 (all y)": (0, 600, 0, 95),
    "far-left x0-96 (all y)": (0, 600, 0, 96),
    "top strip x95-660 y0-100": (0, 100, 95, 660),
    "table area x95-660 y100-600": (100, 600, 95, 660),
    "sidebar x660-800 y0-110": (0, 110, 660, 800),
    "sidebar slots x660-800 y110-600": (110, 600, 660, 800),
    "bottom strip x0-660 y560-600": (560, 600, 0, 660),
}
def L(rel):
    return np.asarray(Image.open(os.path.join(ROOT, rel.replace("/", os.sep))).convert("RGB")).astype(int)
DUP = L("archive_T42/measure_w1_end_x.png")
SCORES = ["archive_T33/measure_w1_end_x.png", "archive_T34/measure_w1_end_x.png",
          "archive_T44/measure_w1_end_x.png", "l3_20261023r/measure_w2_end_x.png", "measure_w1_end_x.png"]
print("V1's own boxes, recomputed:")
print(f"{'region':36s}" + "".join(f"{s.split('/')[0][:13]:>15s}" for s in SCORES))
for name, (y0, y1, x0, x1) in REGIONS.items():
    fr = []
    for s in SCORES:
        a = L(s)
        dd = np.abs(a[y0:y1, x0:x1] - DUP[y0:y1, x0:x1]).max(axis=2)
        fr.append("%.1f%%" % (100.0 * (dd == 0).mean()))
    print(f"{name:36s}" + "".join(f"{x:>15s}" for x in fr))

# where exactly do the 146 left-column pixels live?
a = L("archive_T33/measure_w1_end_x.png"); b = L("archive_T33/measure_w2_end_x.png")
d = np.abs(a - b).max(2)
sub = d[:, 0:120]
ys, xs = np.where(sub > 0)
print("\nleft-edge diff pixels for the T33 pair: n=", len(xs), "distinct cols:", sorted(set(xs.tolist())))
print("row ranges of those pixels:", sorted(set(ys.tolist()))[:5], "...", sorted(set(ys.tolist()))[-5:])
print("cols 0..94 diff count =", int((d[:, 0:95] > 0).sum()), " col 95 diff count =", int((d[:, 95:96] > 0).sum()))
