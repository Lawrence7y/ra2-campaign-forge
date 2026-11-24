"""Read-only probe #7b (mine): colour census of the l3 score-table body, then ASCII of each
row band so digits can be segmented and read; templates come from MY OWN yellow-timer font."""
import os
import numpy as np
from PIL import Image
from collections import Counter

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
P = os.path.join(ROOT, "l3_20261023r", "measure_w2_end_x.png")
a = np.asarray(Image.open(P).convert("RGB"), dtype=np.uint8)

for (r0, r1, tag) in [(194, 216, "row1"), (232, 254, "row2"), (158, 178, "header"), (118, 146, "timerband")]:
    reg = a[r0:r1 + 1, 95:570]
    c = Counter(map(tuple, reg.reshape(-1, 3)))
    print(f"--- {tag} rows {r0}-{r1} top colours:", c.most_common(8))

# ink = far from the modal (background) colour of the band
def inkmask(r0, r1, c0=95, c1=570):
    reg = a[r0:r1 + 1, c0:c1 + 1]
    bg = Counter(map(tuple, reg.reshape(-1, 3))).most_common(1)[0][0]
    d = np.abs(reg.astype(int) - np.array(bg)).sum(2)
    return (d > 150), bg, reg

for (r0, r1, tag) in [(194, 216, "row1"), (232, 254, "row2")]:
    m, bg, reg = inkmask(r0, r1)
    cols = m.any(0)
    runs, x = [], 0
    while x < len(cols):
        if cols[x]:
            y = x
            while y + 1 < len(cols) and cols[y + 1]:
                y += 1
            runs.append((95 + x, 95 + y, int(m[:, x:y + 1].sum())))
            x = y + 1
        else:
            x += 1
    print(f"=== {tag} bg={bg} runs={[rn for rn in runs if rn[2] > 10]}")
    for r in range(m.shape[0]):
        print(f"  {r0+r:3d} " + "".join("#" if v else "." for v in m[r]))
