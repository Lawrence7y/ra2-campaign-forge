# -*- coding: utf-8 -*-
"""§543 Leader 亲算: 冻结窗末截图 = 计分屏？——全量像素分类。

只读 PNG。零真机。
假说：df==0 的「引擎停摆」窗，其窗末截图其实是 RA2 的「遭遇战得分」屏
（= 对局已结束），而非战斗中的引擎停摆。

判据（不依赖 OCR）：
  计分屏面板区域 ≈ x∈[85,625], y∈[110,270]，是大面积**半透明蓝紫**覆盖层；
  战斗画面同区域是地表/单位，色相分布完全不同。
  取该区域中「蓝紫」像素占比 p；并取顶部标题栏区域做第二判据。
对照：frame_target_01.png（开局帧，非计分屏）应 p≈0。
"""
import glob
import os

from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

# 计分屏面板区域（800x600 截图坐标）
PANEL = (85, 108, 625, 272)
# 顶部「遭遇战得分」标题条（右上）
TITLE = (660, 8, 790, 40)


def bluepurple_frac(img, box):
    im = img.convert("RGB").crop(box)
    px = list(im.getdata())
    n = len(px)
    if not n:
        return 0.0
    hit = 0
    for r, g, b in px:
        # 半透明蓝紫：蓝通道显著高于红/绿，且整体偏暗
        if b > r + 18 and b > g + 10 and 40 <= b <= 190 and r < 150:
            hit += 1
    return hit / n


def dark_frac(img, box):
    im = img.convert("RGB").crop(box)
    px = list(im.getdata())
    n = len(px)
    hit = sum(1 for r, g, b in px if (r + g + b) / 3 < 60)
    return hit / n if n else 0.0


rows = []
targets = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png")))
for p in targets:
    try:
        im = Image.open(p)
        im.load()
    except Exception as exc:
        print("  SKIP %s (%s)" % (p, exc))
        continue
    trip = os.path.basename(os.path.dirname(p))
    rows.append((trip, os.path.basename(p), bluepurple_frac(im, PANEL), dark_frac(im, PANEL), im.size))

ctrls = sorted(glob.glob(os.path.join(BASE, "*", "frame_target_01.png")))
print("=== 对照：frame_target_01.png（开局帧）===")
for p in ctrls[:8]:
    try:
        im = Image.open(p)
        im.load()
    except Exception as exc:
        print("  SKIP %s (%s)" % (p, exc))
        continue
    trip = os.path.basename(os.path.dirname(p))
    print("  %-18s p=%.3f dark=%.3f size=%s" % (trip, bluepurple_frac(im, PANEL), dark_frac(im, PANEL), im.size))

print()
print("=== 冻结窗末截图 ===")
print("%-18s %-24s %6s %6s %s" % ("trip", "png", "p", "dark", "size"))
scores = []
for trip, name, p, d, size in rows:
    print("%-18s %-24s %6.3f %6.3f %s" % (trip, name, p, d, size))
    scores.append(p)

print()
if scores:
    scores.sort()
    print("p 分布: min=%.3f p25=%.3f 中位=%.3f p75=%.3f max=%.3f" % (
        scores[0], scores[len(scores) // 4], scores[len(scores) // 2],
        scores[3 * len(scores) // 4], scores[-1]))
    hi = [s for s in scores if s >= 0.5]
    print("p>=0.5 的张数: %d / %d" % (len(hi), len(scores)))
