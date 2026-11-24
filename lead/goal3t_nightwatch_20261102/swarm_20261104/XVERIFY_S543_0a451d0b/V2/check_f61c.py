# -*- coding: utf-8 -*-
from PIL import Image

p = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\archive_T42\measure_w1_end_x.png"
im = Image.open(p)
# Check panel area
PANEL = (85, 108, 630, 275)
c = im.crop(PANEL)
print("Crop size:", c.size)
# What are the dominant colors or content in this image?
colors = sorted(im.getcolors(maxcolors=1000000), key=lambda x: x[0], reverse=True)
print("Top 10 colors in f61c9808:")
for cnt, col in colors[:10]:
    print(f"  color {col}: {cnt} pixels ({cnt/(800*600)*100:.1f}%)")
