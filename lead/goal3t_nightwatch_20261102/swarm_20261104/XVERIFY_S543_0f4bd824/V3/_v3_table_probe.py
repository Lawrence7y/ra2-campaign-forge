# -*- coding: utf-8 -*-
"""V3 独立复算 #14：用**模板匹配**解码 l3_20261023r/w2 比分两行的数字。

不靠肉眼第二次读数。模板来自同一张图上「时间」字段的黄色点阵数字（0-9 已解出），
字体同源；把候选字形二值化后与各数字模板做最优平移对齐 + IoU 匹配。
用于裁定 S543 §四 表里 146 vs 206、171 vs 731 的分歧。
"""
import os

from PIL import Image

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
P = os.path.join(BASE, "l3_20261023r", "measure_w2_end_x.png")

# 已知：时间字段 00:02:56（黄字），从中取 0/2/5/6 模板；其余数字从别的趟取
im = Image.open(P).convert("RGB")
px = im.load()


def is_yellow(x, y):
    r, g, b = px[x, y]
    return r > 170 and g > 150 and b < 130 and (r - b) > 70 and (g - b) > 40


def is_cyan(x, y):
    r, g, b = px[x, y]
    return b > 185 and g > 155 and r < 165


def is_red(x, y):
    r, g, b = px[x, y]
    return r > 165 and g < 130 and b < 130


def segment(x0, x1, y0, y1, pred, gap=1):
    cols = [x for x in range(x0, x1) if any(pred(x, y) for y in range(y0, y1))]
    segs = []
    prev = None
    for x in cols:
        if prev is None or x - prev > gap:
            segs.append([x, x])
        else:
            segs[-1][1] = x
        prev = x
    out = []
    for a, b in segs:
        rows = []
        for y in range(y0, y1):
            line = "".join("#" if pred(xx, y) else "." for xx in range(a, b + 1))
            if "#" in line:
                rows.append(line)
        out.append((a, b, rows))
    return out


# 时间字段模板：00:02:56 -> 位置顺序已知
tb = segment(478, 534, 112, 145, is_yellow)
print("时间字段分段（应为 :00:02:56）:", [(a, b, len(r)) for a, b, r in tb])
TPL = {}
seq_time = [":", "0", "0", ":", "0", "2", ":", "5", "6"]
gi = 0
for (a, b, rows) in tb:
    w = b - a + 1
    if w <= 2:
        continue
    if gi < len(seq_time):
        TPL.setdefault(seq_time[gi], rows)
        gi += 1
print("模板数字:", sorted(TPL))

print()
print("=== 行1（青字 [New Player]）===")
r1 = segment(395, 632, 182, 208, is_cyan)
for a, b, rows in r1:
    print("  字形 x%d-%d w=%d h=%d" % (a, b, b - a + 1, len(rows)))
    for ln in rows:
        print("     " + ln)

print()
print("=== 行2（红字 AI）===")
r2 = segment(395, 632, 226, 252, is_red)
for a, b, rows in r2:
    print("  字形 x%d-%d w=%d h=%d" % (a, b, b - a + 1, len(rows)))
    for ln in rows:
        print("     " + ln)


def iou(a, b):
    ha, wa = len(a), max(len(x) for x in a)
    hb, wb = len(b), max(len(x) for x in b)
    best = 0.0
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            inter = uni = 0
            for y in range(ha):
                for x in range(wa):
                    if a[y][x] != "#":
                        continue
                    Y, X = y + dy, x + dx
                    inside = 0 <= Y < hb and 0 <= X < wb and b[Y][X] == "#"
                    inter += inside
                    uni += 1
            for Y in range(hb):
                for X in range(wb):
                    if b[Y][X] == "#":
                        uni += 0  # counted below
            # union = |A| + |B| - inter
            nb = sum(row.count("#") for row in b)
            na = sum(row.count("#") for row in a)
            uni = na + nb - inter
            if uni:
                best = max(best, inter / uni)
    return best


print()
print("=== 模板匹配（仅 0/2/5/6 有模板；其余给未知）===")
for tag, segs in (("行1", r1), ("行2", r2)):
    line = []
    for a, b, rows in segs:
        if b - a + 1 <= 2:
            line.append(" ")
            continue
        sc = {k: iou(v, rows) for k, v in TPL.items() if k != ":"}
        k, v = max(sc.items(), key=lambda kv: kv[1])
        line.append("%s(%.2f)" % (k, v))
    print("  %s: %s" % (tag, " ".join(line)))
