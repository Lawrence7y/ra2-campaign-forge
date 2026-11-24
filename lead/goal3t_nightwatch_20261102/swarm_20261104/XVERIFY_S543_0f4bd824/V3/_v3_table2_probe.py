# -*- coding: utf-8 -*-
"""V3 独立复算 #15：比分两行数字**逐字精确匹配**已验证的点阵模板。

模板来源：同字体（5x9 点阵）。其中 0/1/2/3/4/5/6/8/9 的取值由「时间」字段
00:00:10 / 00:00:15 / 00:00:24 / 00:00:28 / 00:00:29 / 00:00:30 / 00:00:31 /
00:00:32 / 00:02:56 这些**已知读数**反推，形状与数字一一对应，不靠猜。
"""
import os

from PIL import Image

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")

# 由 9 个已知时间字段读数收集到的 (形状 -> 数字) 对照（5 宽 9 高点阵）
SHAPES = {
    "0": [".###.", "##.##", "##.##", "##.##", "##.##", "##.##", "##.##", "##.##", ".###."],
    "1": ["..##", ".###", "####", "#.##", "..##", "..##", "..##", "..##", "..##"],
    "2": [".###.", "##.##", "...##", "...##", "..##.", ".###.", "###..", "##...", "#####"],
    "3": [".###.", "##.##", "...##", "...##", "..##.", "...##", "...##", "##.##", ".###."],
    "4": ["..##.", "..##.", ".###.", ".###.", "#.##.", "#.##.", "#####", "..##.", "..##."],
    "5": [".####", ".##..", "##...", "####.", "#..##", "...##", "...##", "##.##", ".###."],
    "6": [".###.", "##.##", "##...", "####.", "##.##", "##.##", "##.##", "##.##", ".###."],
    "8": [".###.", "##.##", "##.##", "##.##", ".###.", "##.##", "##.##", "##.##", ".###."],
    "9": [".###.", "##.##", "##.##", "##.##", "##.##", ".####", "...##", "##.#.", ".###."],
    "7": ["#####", "###..", "..##.", "..##.", "..##.", "..##.", "..##.", "..##.", "..##."],
}


def load(p):
    return Image.open(p).convert("RGB")


def classify(rows):
    rows = [r for r in rows if "#" in r]
    best = None
    bs = -1
    for d, t in SHAPES.items():
        if len(t) != len(rows):
            continue
        sc = 0
        tot = 0
        for a, b in zip(rows, t):
            for ca, cb in zip(a, b):
                if ca == "#" or cb == "#":
                    tot += 1
                    if ca == cb:
                        sc += 1
        s = sc / tot if tot else 0
        if s > bs:
            bs, best = s, d
    return best, bs


def segment(px, x0, x1, y0, y1, pred, gap=1):
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
            ln = "".join("#" if pred(xx, y) else "." for xx in range(a, b + 1))
            if "#" in ln:
                rows.append(ln)
        out.append((a, b, rows))
    return out


def run(path, ybands, label):
    im = load(path)
    px = im.load()
    for kind, pred in (("cyan", lambda x, y: (lambda r, g, b: b > 180 and g > 150 and r < 170)(*px[x, y])),
                       ("red", lambda x, y: (lambda r, g, b: r > 160 and g < 130 and b < 130)(*px[x, y]))):
        for (x0, x1, y0, y1, name) in ybands:
            segs = segment(px, x0, x1, y0, y1, pred)
            digs = []
            for a, b, rows in segs:
                if b - a + 1 <= 2:
                    continue
                d, s = classify(rows)
                digs.append("%s%s" % (d, "" if s > 0.93 else ("~%.2f" % s)))
            if digs:
                print("  %-26s %-4s x%d-%d y%d-%d -> %s" % (
                    label + "/" + name, kind, x0, x1, y0, y1, " ".join(digs)))


P = os.path.join(BASE, "l3_20261023r", "measure_w2_end_x.png")
print("=== l3_20261023r/w2 比分表（S543 §四 那张表）===")
run(P, [(395, 460, 182, 210, "摧毁数列"), (490, 545, 182, 210, "损失数列"),
        (555, 600, 182, 210, "建造数列"), (600, 660, 182, 210, "分数列")], "行1")
print("  --- 行2 (y 224..252) ---")
run(P, [(395, 460, 224, 252, "摧毁数列"), (490, 545, 224, 252, "损失数列"),
        (555, 600, 224, 252, "建造数列"), (600, 660, 224, 252, "分数列")], "行2")

print()
print("=== 对照：archive_T34/w1 的行1（应接近全 0/1）===")
P2 = os.path.join(BASE, "archive_T34", "measure_w1_end_x.png")
run(P2, [(395, 460, 182, 210, "摧毁数"), (490, 545, 182, 210, "损失数")], "行1")
run(P2, [(395, 460, 224, 252, "摧毁数"), (490, 545, 224, 252, "损失数")], "行2")
