# -*- coding: utf-8 -*-
import hashlib
from PIL import Image

p = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\archive_T42\measure_w1_end_x.png"
im = Image.open(p)
print("Format:", im.format, "Size:", im.size, "Mode:", im.mode)
# Inspect some pixels
colors = im.getcolors(maxcolors=1000000)
print(f"Total distinct colors: {len(colors) if colors else 'many'}")
# Check bbox or corners
print("Corner (0,0):", im.getpixel((0,0)))
print("Center (400,300):", im.getpixel((400,300)))
print("Corner (799,599):", im.getpixel((799,599)))
