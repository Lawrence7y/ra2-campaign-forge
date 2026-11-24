# -*- coding: utf-8 -*-
"""§543: 判别器 —— 计分屏计时器在对局冻结期间是「冻结」还是「继续走」？

若 timer 在 w1_end 与 w2_end 同值 ⇒ 该屏是静态结算屏（对局已结束）。
若 timer 在 w2_end 更大 ⇒ 计时仍在走（说明不是「对局结束」而是别的东西）。

同时输出每趟 w1/w2 的判据 p（蓝紫面板占比）与 frame 号，便于对账。
"""
import glob
import os

from PIL import Image, ImageDraw

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUT = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\_leader_timer_w1_vs_w2.png"

TIMER = (430, 118, 640, 150)
PANEL = (85, 108, 630, 275)
SCALE = 3


def panel_p(im):
    c = im.convert("RGB").crop(PANEL)
    px = c.get_flattened_data() if hasattr(c, "get_flattened_data") else list(c.getdata())
    n = len(px)
    hit = sum(1 for r, g, b in px if b > r + 18 and b > g + 10 and 40 <= b <= 190 and r < 150)
    return hit / n if n else 0.0


rows = []
for d in sorted(os.listdir(BASE)):
    tripdir = os.path.join(BASE, d)
    if not os.path.isdir(tripdir):
        continue
    for w in (1, 2):
        p = os.path.join(tripdir, "measure_w%d_end_x.png" % w)
        if not os.path.exists(p):
            continue
        try:
            im = Image.open(p)
            im.load()
        except Exception:
            continue
        rows.append((d, w, p, panel_p(im), im))

# 只保留有 w1 且 w2 的趟，做上下对照
by_trip = {}
for d, w, p, pv, im in rows:
    by_trip.setdefault(d, {})[w] = (p, pv, im)

strips = []
labels = []
for d in sorted(by_trip):
    ws = by_trip[d]
    for w in sorted(ws):
        p, pv, im = ws[w]
        c = im.convert("RGB").crop(TIMER)
        c = c.resize((c.width * SCALE, c.height * SCALE), Image.LANCZOS)
        strips.append(c)
        labels.append("%s  w%d  p=%.3f" % (d, w, pv))

print("%-20s %3s %7s" % ("trip", "win", "panel_p"))
for d, w, p, pv, im in rows:
    print("%-20s %3d %7.3f" % (d, w, pv))

w_max = max(s.width for s in strips)
h = sum(s.height + 15 for s in strips)
canvas = Image.new("RGB", (w_max, h), (10, 10, 12))
dr = ImageDraw.Draw(canvas)
y = 0
for s, lab in zip(strips, labels):
    dr.text((4, y + 2), lab, fill=(120, 255, 160) if "p=0.0" in lab else (255, 230, 120))
    y += 15
    canvas.paste(s, (0, y))
    y += s.height
canvas.save(OUT)
print("saved", OUT, canvas.size)
