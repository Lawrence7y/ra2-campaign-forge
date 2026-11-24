# -*- coding: utf-8 -*-
"""§543: T38 w1 vs w2 计时器逐像素对照（唯一一处 w1/w2 计时器不同）。

若计时器在帧号冻结期间仍前进 ⇒ 「屏幕时间 = 帧号/31.2」的映射不成立，
必须查清它到底在数什么。放大并排，标出差异框。
"""
import os

from PIL import Image, ImageChops, ImageDraw

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUT = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\_leader_t38_timer.png"

# 放宽区域，含「时间」标签与数值
BOX = (420, 110, 650, 155)
SCALE = 5

a = Image.open(os.path.join(BASE, "archive_T38", "measure_w1_end_x.png")).convert("RGB")
a.load()
b = Image.open(os.path.join(BASE, "archive_T38", "measure_w2_end_x.png")).convert("RGB")
b.load()
ca = a.crop(BOX)
cb = b.crop(BOX)
diff = ImageChops.difference(ca, cb).convert("L")
print("diff bbox(局部):", diff.getbbox(), "max:", max(diff.getextrema()))

ca = ca.resize((ca.width * SCALE, ca.height * SCALE), Image.LANCZOS)
cb = cb.resize((cb.width * SCALE, cb.height * SCALE), Image.LANCZOS)

w = ca.width
h = ca.height * 2 + 40
canvas = Image.new("RGB", (w, h), (10, 10, 12))
d = ImageDraw.Draw(canvas)
d.text((4, 3), "T38 w1  (frame 940)", fill=(255, 230, 120))
canvas.paste(ca, (0, 18))
d.text((4, ca.height + 22), "T38 w2  (frame 940)", fill=(120, 255, 160))
canvas.paste(cb, (0, ca.height + 36))
canvas.save(OUT)
print("saved", OUT, canvas.size)
