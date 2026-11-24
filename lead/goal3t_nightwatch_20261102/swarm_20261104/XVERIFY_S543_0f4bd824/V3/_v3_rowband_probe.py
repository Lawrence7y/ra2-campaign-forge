# -*- coding: utf-8 -*-
"""V3 独立复算 #3：不靠猜坐标，直接测「哪些 y 行在不同趟之间逐像素相同」。

若两张来自**不同趟**的末截图是同一类静态屏（计分屏），其固定位图字
（标题 / 列名 / 分隔线）应在若干 y 行上逐像素全等；而战斗画面不可能。
据此客观定位「计分屏固定文字带」，再用该带对全仓 PNG 做分离度检验。
"""
import collections
import glob
import hashlib
import json
import os

from PIL import Image

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
X0, X1 = 85, 630


def load(p):
    try:
        im = Image.open(p).convert("RGB")
    except Exception:
        return None
    return im if im.size == (800, 600) else None


def rowhash(im, y):
    return hashlib.sha256(im.crop((X0, y, X1, y + 1)).tobytes()).hexdigest()


def rows(im, y0, y1):
    return [rowhash(im, y) for y in range(y0, y1)]


end = {}
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png"))):
    im = load(p)
    if im is None:
        continue
    end[(os.path.basename(os.path.dirname(p)), os.path.basename(p))] = im

# 选两张确定是计分屏、且来自不同趟、帧号差很大的：T34/w1 (f=302) 与 T40/w1 (f=908)
a = end[("archive_T34", "measure_w1_end_x.png")]
b = end[("archive_T40", "measure_w1_end_x.png")]
ra, rb = rows(a, 100, 290), rows(b, 100, 290)
same = [100 + i for i in range(len(ra)) if ra[i] == rb[i]]
print("=== T34/w1(f=302) vs T40/w1(f=908) 在 x[%d,%d) 上逐像素相同的 y 行 ===" % (X0, X1))
print("  共 %d 行相同 / 190 行" % len(same))
# 连续段
segs = []
for y in same:
    if segs and y == segs[-1][1] + 1:
        segs[-1][1] = y
    else:
        segs.append([y, y])
for s in segs:
    print("    y %d..%d  (h=%d)" % (s[0], s[1], s[1] - s[0] + 1))

print()
print("=== 用「固定文字带」y=%d..%d 做全仓 PNG 分离度 ===" % (segs[0][0], segs[-1][1]))
Y0, Y1 = segs[0][0], segs[-1][1] + 1


def band(im):
    hs = "".join(rowhash(im, y) for y in range(Y0, Y1))
    return hashlib.sha256(hs.encode()).hexdigest()[:12]

# 先看该带在 25 张末截图上的分布
print("%-18s %-26s band" % ("trip", "png"))
groups = collections.defaultdict(list)
for (t, n), im in sorted(end.items()):
    bh = band(im)
    groups[bh].append("%s/%s" % (t, n))
    print("%-18s %-26s %s" % (t, n, bh))
print()
print("  末截图 band 组数：%d / 25" % len(groups))
for k, v in sorted(groups.items(), key=lambda kv: -len(kv[1])):
    print("    %s n=%d %s" % (k, len(v), v if len(v) <= 8 else "(%d imgs)" % len(v)))

main = max(groups, key=lambda k: len(groups[k]))
score_bands = {k for k, v in groups.items() if len(v) >= 1}

print()
print("=== 对照：全仓其它 800x600 PNG 是否也命中这些 band ===")
hits = []
tot = 0
for p in sorted(glob.glob(os.path.join(BASE, "**", "*.png"), recursive=True)):
    if "measure_w" in os.path.basename(p):
        continue
    im = load(p)
    if im is None:
        continue
    tot += 1
    bh = band(im)
    if bh in groups:
        hits.append((os.path.relpath(p, BASE), bh, groups[bh][0]))
print("  对照 PNG 共 %d 张；命中末截图 band 者 %d 张" % (tot, len(hits)))
for r, bh, ex in hits:
    print("      %-52s band=%s  与 %s 同带" % (r, bh, ex))
