#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在抓图上标注 T1 检测到的 tile bbox + 中心十字，作为可视化证据（不改原图）。"""
import os, json
from PIL import Image, ImageDraw

EVID = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-I\EVIDENCE"
grid = json.load(open(os.path.join(EVID, "sidebar_grid.json"), encoding="utf-8"))
img = Image.open(os.path.join(EVID, "t1_fresh.png")).convert("RGB")
d = ImageDraw.Draw(img)
ch = grid["chosen"]
x0, y0, x1, y1 = ch["bbox"]
cx, cy = ch["center"]
# 画所有槽 bbox（淡），选中槽（亮红），中心十字（黄）
for t in grid["tiles"]:
    a, b, c, e = t["bbox"]
    d.rectangle([a, b, c, e], outline=(90, 90, 90), width=1)
d.rectangle([x0, y0, x1, y1], outline=(255, 40, 40), width=3)
d.line([cx-10, cy, cx+10, cy], fill=(255, 255, 0), width=2)
d.line([cx, cy-10, cx, cy+10], fill=(255, 255, 0), width=2)
d.text((x0, y0-16), "NAPOWR center=(%d,%d)" % (cx, cy), fill=(255, 255, 0))
# 裁侧栏区域放大
crop = img.crop((2246, 400, 2560, 900)).resize((628, 1000))
crop.save(os.path.join(EVID, "t1_detected_annotated.png"))
print("saved t1_detected_annotated.png; center", (cx, cy), "bbox", ch["bbox"])
