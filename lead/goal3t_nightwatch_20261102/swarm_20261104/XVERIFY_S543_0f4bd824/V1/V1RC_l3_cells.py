"""Read-only probe #7c (mine): dump raw pixels of the disputed table cells of l3 score screen
as ASCII under several candidate ink masks, narrow windows so lines are readable."""
import os
import numpy as np
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
a = np.asarray(Image.open(os.path.join(ROOT, "l3_20261023r", "measure_w2_end_x.png")).convert("RGB"), dtype=np.int16)
BLUE = np.array([33, 105, 214])
RED = np.array([255, 24, 24])

def show(r0, r1, c0, c1, tag):
    reg = a[r0:r1 + 1, c0:c1 + 1]
    print(f"### {tag} rows {r0}-{r1} cols {c0}-{c1}")
    for name, ref in (("blue", BLUE), ("red", RED)):
        d = np.abs(reg - ref).sum(2)
        for th in (90, 200):
            m = d < th
            print(f"  -- mask close-to-{name} sum<{th}  (npix={int(m.sum())})")
            for i in range(m.shape[0]):
                print(f"    {r0+i:3d} " + "".join("#" if v else "." for v in m[i]))

show(194, 212, 330, 380, "row1 second-column digits (the disputed 146-vs-206)")
show(232, 250, 330, 380, "row2 second-column digits (the disputed 171-vs-731)")
