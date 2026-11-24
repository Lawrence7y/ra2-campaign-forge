"""Crop the score-table header of a known score screen so the timer field can be located by eye."""
import os
import numpy as np
from PIL import Image, ImageDraw

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
OUT = r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/V2/pix"
os.makedirs(OUT, exist_ok=True)

im = Image.open(os.path.join(R, "archive_T33", "measure_w1_end_x.png")).convert("RGB")
a = np.asarray(im).astype(np.int16)
ref = np.asarray(Image.open(os.path.join(R, "archive_T33", "measure_w2_end_x.png")).convert("RGB")).astype(np.int16)
d = np.abs(a - ref).max(axis=2)
# tight bbox of the table region: rows/cols where many pixels differ
rows = np.where((d > 24).sum(axis=1) > 100)[0]
cols = np.where((d > 24).sum(axis=0) > 100)[0]
print("[T1] table-ish rows", rows.min(), rows.max(), "cols", cols.min(), cols.max())
# print a coarse occupancy grid to find the header row band
band = (d > 24).sum(axis=1)
for y in range(0, 600, 10):
    print(f"    y {y:3d}-{y+9:3d}: px_differing_in_band {int(band[y:y+10].sum()):7d}")

# whole upper half at 3x with a 25px grid so coordinates can be read off
big = im.crop((0, 60, 800, 320)).resize((2400, 780), Image.NEAREST)
dr = ImageDraw.Draw(big)
for x in range(0, 2400, 75):
    dr.line([(x, 0), (x, 780)], fill=(255, 0, 255), width=1)
    dr.text((x + 2, 2), str(x // 3), fill=(255, 255, 0))
for y in range(0, 780, 75):
    dr.line([(0, y), (2400, y)], fill=(255, 0, 255), width=1)
    dr.text((2, y + 2), str(60 + y // 3), fill=(255, 255, 0))
big.save(os.path.join(OUT, "T33w1_header_3x_grid.png"))
print("[T2] wrote", os.path.join(OUT, "T33w1_header_3x_grid.png"), big.size)
