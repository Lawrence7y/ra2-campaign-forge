import numpy as np
from PIL import Image

p = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l3_20261023r\measure_w2_end_x.png"
im = Image.open(p).convert("RGB")
arr = np.array(im)

# Let's find coordinates of red text in row 2
# Red text: high R (e.g. R > 150), and R > 2 * G and R > 2 * B
mask = (arr[:, :, 0] > 120) & (arr[:, :, 0] > 2 * arr[:, :, 1]) & (arr[:, :, 0] > 2 * arr[:, :, 2])
y_indices, x_indices = np.where(mask)
print(f"Red pixels found: {len(y_indices)}")
print(f"y range: {y_indices.min()}..{y_indices.max()}")
print(f"x range: {x_indices.min()}..{x_indices.max()}")

# Group by connected components or inspect regions
for y0 in range(y_indices.min(), y_indices.max() + 1):
    row_pixels = mask[y0, 250:600]
    s = "".join("#" if px else " " for px in row_pixels)
    if "#" in s:
        print(f"y={y0:3d} (x:250..600): {s}")
