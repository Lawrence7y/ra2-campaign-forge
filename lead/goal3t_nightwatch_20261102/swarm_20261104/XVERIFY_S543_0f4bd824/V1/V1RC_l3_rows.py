"""Read-only probe #7 (mine): locate the score-table body of l3_20261023r/measure_w2_end_x.png
without assuming anyone's coordinates, then print each digit cell as ASCII so I can read it,
and template-match against the font I derived from the yellow timer (my own 5x9 templates)."""
import os
import numpy as np
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
P = os.path.join(ROOT, "l3_20261023r", "measure_w2_end_x.png")
a = np.asarray(Image.open(P).convert("RGB"), dtype=np.int16)
print("shape", a.shape)
# row profile of 'strongly coloured / bright' pixels below the header row
lum = a.max(2) - a.min(2)
bright = (a.max(2) > 150)
for r in range(150, 300):
    n = int(bright[r, 90:570].sum())
    if n:
        print(f"row {r:3d} bright_cols(90..569)={n:4d}")
