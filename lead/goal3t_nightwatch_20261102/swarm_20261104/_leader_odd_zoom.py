# -*- coding: utf-8 -*-
"""§543: 单张放大核对（T38 w1、T42 w1、T42 w2、T33 w2）。

这几个的判据 p 与计时器读数与其余不同，必须逐张看清，不能靠拼图凑读。
"""
import os

from PIL import Image, ImageDraw

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUT = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\_leader_odd_zoom.png"

picks = [
    ("archive_T38", "measure_w1_end_x.png"),
    ("archive_T42", "measure_w1_end_x.png"),
    ("archive_T42", "measure_w2_end_x.png"),
    ("archive_T33", "measure_w2_end_x.png"),
]

SCALE = 2
tiles = []
labels = []
for trip, name in picks:
    p = os.path.join(BASE, trip, name)
    im = Image.open(p)
    im.load()
    full = im.convert("RGB").resize((im.width // SCALE, im.height // SCALE), Image.LANCZOS)
    tiles.append(full)
    labels.append("%s %s" % (trip, name))
    print("tile", trip, name, full.size)

cols = 2
rows = (len(tiles) + cols - 1) // cols
tw, th = tiles[0].size
canvas = Image.new("RGB", (tw * cols, (th + 16) * rows), (12, 12, 14))
d = ImageDraw.Draw(canvas)
for i, (t, lab) in enumerate(zip(tiles, labels)):
    cx = (i % cols) * tw
    cy = (i // cols) * (th + 16)
    d.text((cx + 4, cy + 3), lab, fill=(255, 230, 120))
    canvas.paste(t, (cx, cy + 16))
canvas.save(OUT)
print("saved", OUT, canvas.size)
