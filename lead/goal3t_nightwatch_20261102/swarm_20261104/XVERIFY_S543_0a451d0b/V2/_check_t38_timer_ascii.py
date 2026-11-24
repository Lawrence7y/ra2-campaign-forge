# -*- coding: utf-8 -*-
import os
from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

for w in [1, 2]:
    p = os.path.join(BASE, "archive_T38", f"measure_w{w}_end_x.png")
    im = Image.open(p).convert("RGB")
    crop = im.crop((420, 110, 650, 155))
    w_px, h_px = crop.size
    print(f"\n=== T38 w{w} timer ASCII (box: 420, 110, 650, 155) ===")
    lines = []
    for y in range(h_px):
        row = ""
        for x in range(w_px):
            r, g, b = crop.getpixel((x, y))
            # 黄色字检测
            if r > 150 and g > 150 and b < 100:
                row += "#"
            elif r > 100 and g > 100 and b < 80:
                row += "."
            else:
                row += " "
        if "#" in row or "." in row:
            lines.append(f"{y:02d}: {row}")
    for l in lines:
        print(l)
