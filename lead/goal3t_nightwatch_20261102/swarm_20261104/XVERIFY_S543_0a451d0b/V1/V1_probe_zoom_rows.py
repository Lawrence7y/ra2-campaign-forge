import os
import numpy as np
from PIL import Image

p = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l3_20261023r\measure_w2_end_x.png"
im = Image.open(p).convert("RGB")
arr = np.array(im)

# Let's save a clean zoomed-in image of:
# Row 1 (blue text, y: 160..190, x: 80..620)
# Row 2 (red text,  y: 220..250, x: 80..620)
OUT_DIR = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\XVERIFY_S543_0a451d0b\V1"

im_row1 = im.crop((80, 160, 620, 190)).resize(((620-80)*3, 30*3), Image.Resampling.NEAREST)
im_row2 = im.crop((80, 220, 620, 250)).resize(((620-80)*3, 30*3), Image.Resampling.NEAREST)

im_row1.save(os.path.join(OUT_DIR, "V1_l3_row1_blue.png"))
im_row2.save(os.path.join(OUT_DIR, "V1_l3_row2_red.png"))

print("Saved row1 and row2 images.")
