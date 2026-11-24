# -*- coding: utf-8 -*-
from PIL import Image
import collections

p = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\archive_T33\measure_w2_end_x.png"
im = Image.open(p)
colors = im.getcolors(maxcolors=1000000)
print("Total unique colors:", len(colors))
top_colors = sorted(colors, reverse=True)[:10]
for count, col in top_colors:
    print(f"  color {col}: count={count} ({count/(800*600)*100:.2f}%)")
