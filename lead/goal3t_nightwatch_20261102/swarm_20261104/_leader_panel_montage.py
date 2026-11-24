# -*- coding: utf-8 -*-
"""§543: 把「冻结窗末截图」的计分屏面板裁出来拼成一张对照图（只读 PNG）。

面板区域固定 (85,108)-(630,275)。纵向堆叠，便于一次目视核对多趟的
「时间 / 摧毁数 / 分数」字段，与我算的 frame/31 对账。
"""
import os

from PIL import Image, ImageDraw

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUT = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\_leader_scorescreen_montage.png"

PANEL = (85, 108, 630, 275)

picks = [
    ("archive_T33", "measure_w1_end_x.png"),
    ("archive_T34", "measure_w1_end_x.png"),
    ("archive_T36", "measure_w1_end_x.png"),
    ("archive_T38", "measure_w1_end_x.png"),
    ("archive_T41", "measure_w1_end_x.png"),
    ("archive_T43", "measure_w1_end_x.png"),
    ("archive_T49_u0800", "measure_w1_end_x.png"),
    ("l3_20261023r", "measure_w2_end_x.png"),
]

crops = []
labels = []
for trip, name in picks:
    p = os.path.join(BASE, trip, name)
    if not os.path.exists(p):
        print("MISSING", p)
        continue
    im = Image.open(p)
    im.load()
    c = im.convert("RGB").crop(PANEL)
    crops.append(c)
    labels.append("%s/%s" % (trip, name))
    print("crop %-34s %s" % (labels[-1], c.size))

w = max(c.width for c in crops)
h = sum(c.height for c in crops) + 14 * len(crops)
canvas = Image.new("RGB", (w, h), (24, 24, 28))
d = ImageDraw.Draw(canvas)
y = 0
for c, lab in zip(crops, labels):
    d.text((4, y + 2), lab, fill=(255, 230, 120))
    y += 14
    canvas.paste(c, (0, y))
    y += c.height
canvas.save(OUT)
print("saved", OUT, canvas.size)
