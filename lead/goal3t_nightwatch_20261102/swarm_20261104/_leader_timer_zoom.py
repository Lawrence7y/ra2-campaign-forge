# -*- coding: utf-8 -*-
"""§543: 放大计分屏「时间」字段（右上），逐趟核对 timer 与 frame/31 的一致性。

只读 PNG。输出单张拼接图，便于一次目视。
"""
import os

from PIL import Image, ImageDraw

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUT = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\_leader_timer_zoom.png"

# 「时间」字段（"时 间" 标签 + HH:MM:SS）在 800x600 图中的位置
TIMER = (430, 118, 620, 148)
SCALE = 4

picks = [
    ("archive_T33", "measure_w1_end_x.png"),
    ("archive_T34", "measure_w1_end_x.png"),
    ("archive_T36", "measure_w1_end_x.png"),
    ("archive_T38", "measure_w1_end_x.png"),
    ("archive_T39", "measure_w2_end_x.png"),
    ("archive_T41", "measure_w1_end_x.png"),
    ("archive_T43", "measure_w1_end_x.png"),
    ("archive_T49_u0800", "measure_w1_end_x.png"),
    ("l3_20261023r", "measure_w2_end_x.png"),
]

strips = []
labels = []
for trip, name in picks:
    p = os.path.join(BASE, trip, name)
    if not os.path.exists(p):
        print("MISSING", p)
        continue
    im = Image.open(p)
    im.load()
    c = im.convert("RGB").crop(TIMER)
    c = c.resize((c.width * SCALE, c.height * SCALE), Image.LANCZOS)
    strips.append(c)
    labels.append("%s" % trip)

w = max(s.width for s in strips)
h = sum(s.height + 16 for s in strips)
canvas = Image.new("RGB", (w, h), (10, 10, 12))
d = ImageDraw.Draw(canvas)
y = 0
for s, lab in zip(strips, labels):
    d.text((4, y + 3), lab, fill=(255, 230, 120))
    y += 16
    canvas.paste(s, (0, y))
    y += s.height
canvas.save(OUT)
print("saved", OUT, canvas.size)
