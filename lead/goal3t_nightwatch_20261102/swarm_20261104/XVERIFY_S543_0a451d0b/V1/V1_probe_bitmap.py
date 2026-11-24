import numpy as np
from PIL import Image

p = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l3_20261023r\measure_w2_end_x.png"
im = Image.open(p).convert("RGB")
arr = np.array(im)

# Let's inspect the losses column
# In row 2 (red): y is around 200..215, x is around 380..420
# Let's print the RGB values in this region to see the exact bitmap!
# Red color has high R, low G, low B
red_region = arr[200:220, 375:415]
print("=== RED LOSSES BITMAP ===")
for r_idx in range(red_region.shape[0]):
    row_str = ""
    for c_idx in range(red_region.shape[1]):
        r, g, b = red_region[r_idx, c_idx]
        if r > 150 and g < 50 and b < 50:
            row_str += "#"
        elif r > 80 and g < 40 and b < 40:
            row_str += "."
        else:
            row_str += " "
    if "#" in row_str or "." in row_str:
        print(f"{200+r_idx:3d}: {row_str}")

# Let's inspect the score column for '126800' to see '1' and '2' and '6'
print("\n=== RED SCORE BITMAP (126800) ===")
score_region = arr[200:220, 520:585]
for r_idx in range(score_region.shape[0]):
    row_str = ""
    for c_idx in range(score_region.shape[1]):
        r, g, b = score_region[r_idx, c_idx]
        if r > 150 and g < 50 and b < 50:
            row_str += "#"
        elif r > 80 and g < 40 and b < 40:
            row_str += "."
        else:
            row_str += " "
    if "#" in row_str or "." in row_str:
        print(f"{200+r_idx:3d}: {row_str}")
