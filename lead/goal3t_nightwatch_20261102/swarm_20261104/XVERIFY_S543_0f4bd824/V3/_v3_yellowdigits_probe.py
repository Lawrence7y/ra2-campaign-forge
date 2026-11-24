# -*- coding: utf-8 -*-
"""V3 独立复算 #7：把「时间」数字单独抠出来做指纹——不用 OCR，不用整块矩形哈希。

问题：Leader 用 (430,118,640,150) 矩形哈希判「计时器逐像素相同」。该矩形含背景，
而本件实测 w1/w2 整幅图有 549~2682 个像素在变，矩形哈希会被背景变化污染，
既可能假阴（数字相同但背景不同 -> 判成"不同"），也可能假阳。

做法：在标题行里只取**亮黄色位图像素**（计分屏数字/标签的颜色）的集合，
按 x 排序取其掩码作为指纹。背景变化不影响黄色掩码。
"""
import collections
import glob
import hashlib
import json
import os

from PIL import Image

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
ROW = (85, 112, 630, 152)          # 计分屏标题行（含 游戏:1 与 时间:HH:MM:SS）


def load(p):
    try:
        im = Image.open(p).convert("RGB")
    except Exception:
        return None
    return im if im.size == (800, 600) else None


def yellow_mask(im, box=ROW):
    c = im.crop(box)
    w, h = c.size
    px = c.tobytes()
    m = []
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 3
            r, g, b = px[i], px[i + 1], px[i + 2]
            if r > 170 and g > 150 and b < 130 and (r - b) > 70 and (g - b) > 40:
                m.append((x, y))
    return m, w, h


def sig(im):
    m, w, h = yellow_mask(im)
    pts = sorted(m)
    return hashlib.sha256(str(pts).encode()).hexdigest()[:12], len(pts), w, h


print("先验证黄色掩码定位是否稳定（一张计分屏）：")
im = load(os.path.join(BASE, "archive_T34", "measure_w1_end_x.png"))
m, w, h = yellow_mask(im)
xs = [x for x, y in m]
ys = [y for x, y in m]
print("  命中 %d 像素  x %d..%d  y %d..%d  (crop %dx%d 起点 %s)" % (
    len(m), min(xs), max(xs), min(ys), max(ys), w, h, ROW[:2]))

print()
print("=== 25 张末截图的「黄色位图指纹」分组 ===")
recs = []
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png"))):
    im = load(p)
    if im is None:
        continue
    trip = os.path.basename(os.path.dirname(p))
    win = os.path.basename(p).split("_")[1]
    jp = os.path.join(os.path.dirname(p), "measure_%s.json" % win)
    f1 = None
    if os.path.exists(jp):
        ed = (json.load(open(jp, encoding="utf-8")).get("frame_edges") or [])
        f1 = ed[-1][0] if ed else None
    s, n, _, _ = sig(im)
    recs.append((trip, win, f1, s, n))

g = collections.defaultdict(list)
for trip, win, f1, s, n in recs:
    g[s].append((trip, win, f1, n))
for s, v in sorted(g.items(), key=lambda kv: -len(kv[1])):
    print("  sig=%s n=%d  frames=%s" % (s, len(v), sorted(set(str(x[2]) for x in v))))
    for trip, win, f1, n in v:
        print("        %-20s w%s f1=%-6s 黄像素数=%d" % (trip, win, f1, n))

print()
print("=== 单调性检验：同组内帧号跨度 -> 是否可能同显一秒 ===")
for s, v in g.items():
    fs = sorted(x[2] for x in v if x[2] is not None)
    if len(fs) > 1:
        print("  sig=%s 帧 %s 跨度 %d  = %.2f s @31.2 / %.2f s @30" % (
            s, fs, fs[-1] - fs[0], (fs[-1] - fs[0]) / 31.2, (fs[-1] - fs[0]) / 30.0))

print()
print("=== 关键对照：f=940 与 f=945 应显示同一秒（30.1 与 30.3）===")
for trip, win, f1, s, n in recs:
    if f1 in (940, 945, 908, 883, 860, 845):
        print("  %-20s w%s f1=%-5s sig=%s" % (trip, win, f1, s))
