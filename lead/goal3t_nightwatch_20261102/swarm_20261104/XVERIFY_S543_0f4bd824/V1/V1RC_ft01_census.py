"""Read-only probe #14 (mine): census of frame_target_01.png across the whole trip tree,
classified with MY structural test (title-band ink == 361 and header-row ink == 993).
Tests S543 Sec 7.6 ('15 张 frame_target_01 命中面板判据'), which V1 did not check."""
import os, glob
import numpy as np
from PIL import Image

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
fs = sorted(glob.glob(os.path.join(R, "**", "frame_target_01.png"), recursive=True))
print("frame_target_01.png files:", len(fs))
hit, nohit, bad = [], [], []
for p in fs:
    rel = os.path.relpath(p, R).replace("\\", "/")
    try:
        a = np.asarray(Image.open(p).convert("RGB"), dtype=np.int16)
    except Exception as e:
        bad.append((rel, type(e).__name__, os.path.getsize(p)))
        continue
    m = (a[..., 0] > 200) & (a[..., 1] > 200) & (a[..., 2] < 110) & ((a[..., 0] - a[..., 2]) > 60)
    t, h = int(m[9:24, 400:800].sum()), int(m[160:175, 99:529].sum())
    (hit if (t == 361 and h == 993) else nohit).append((rel, t, h, a.shape[1], a.shape[0]))
print("SCORE-layout hits:", len(hit))
for x in hit:
    print("   ", x)
print("NOT score:", len(nohit))
for x in nohit:
    print("   ", x)
print("unreadable:", len(bad), bad)
