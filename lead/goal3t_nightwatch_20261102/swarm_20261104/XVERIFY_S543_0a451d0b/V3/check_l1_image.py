# -*- coding: utf-8 -*-
import os
from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
p = os.path.join(BASE, "l1_20261023e4", "measure_w2_end_x.png")
if os.path.exists(p):
    im = Image.open(p)
    print("l1_20261023e4/measure_w2_end_x.png exists, size:", im.size)
    # resize small to view or check colors
    colors = im.getcolors(maxcolors=100000)
    print("Unique colors:", len(colors) if colors else ">100000")
else:
    print("File not found")
