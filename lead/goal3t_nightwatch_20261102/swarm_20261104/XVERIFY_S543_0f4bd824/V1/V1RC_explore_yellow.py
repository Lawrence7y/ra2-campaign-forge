"""Exploratory (read-only): locate pure-yellow glyph pixels in the end-window screenshots,
so that the score-screen field coordinates are MINE, not the report's."""
import glob, os
import numpy as np
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

files = sorted(glob.glob(os.path.join(ROOT, "**", "measure_w*_end_*.png"), recursive=True))
print("n_files_recursive:", len(files))
for f in files:
    a = np.asarray(Image.open(f).convert("RGB"), dtype=np.int16)
    h, w, _ = a.shape
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    ymask = (R > 230) & (G > 230) & (B < 70)
    n = int(ymask.sum())
    if n:
        rows = np.where(ymask.any(1))[0]
        cols = np.where(ymask.any(0))[0]
        # row bands
        bands = []
        prev = -5
        start = None
        for r in range(h):
            if ymask[r].any():
                if start is None:
                    start = r
            else:
                if start is not None and r - 1 >= start:
                    bands.append((start, r - 1, int(ymask[start:r].sum())))
                    start = None
        if start is not None:
            bands.append((start, h - 1, int(ymask[start:].sum())))
        bands = [b for b in bands if b[2] > 30]
        rel = os.path.relpath(f, ROOT).replace("\\", "/")
        print(f"{rel:52s} {w}x{h} yellow={n:6d} xrange=({cols.min()},{cols.max()}) bands(r0,r1,npix)={bands}")
    else:
        rel = os.path.relpath(f, ROOT).replace("\\", "/")
        print(f"{rel:52s} {w}x{h} yellow=0")
