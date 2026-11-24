# -*- coding: utf-8 -*-
"""V3 独立复算 #13：把计分屏上的数字**逐字解码**（模板匹配，非肉眼、非猜）。

字形模板由本件自己从像素里聚类得到（13 个形状，见 _v3_glyphdict），
再按 RA2 点阵字形人工对应 0-9 与冒号。然后自动解出：
  - 25 张末截图的「时间」字段（HH:MM:SS）
  - l3_20261023r/w2 两行比分的每个数字
并对 S543 §二 的「时间 = 帧号/31.2」做量化检验。
"""
import glob
import hashlib
import json
import os

from PIL import Image

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")

# 由 _v3_glyph_probe 聚类出的形状 -> 数字（依据点阵形态：0 闭合环、1 左上一撇右竖、
# 2 顶弧+斜降+底横、3 双右弧、4 左斜+横+右竖、5 顶横+左竖+下环、6 下环带左尾、
# 8 双环、9 上环带右尾）
GLY = {
    "1f997d": "0", "1c95e5": "1", "83c50a": "2", "28b1bf": "4", "94ea9d": "8",
    "49d82d": "9", "f9dfba": "3", "52af2d": "5", "41fd3c": "6",
    "6da38b": ":", "70cbea": ":",
}
LABEL = {"173724", "d92d79"}


def load(p):
    try:
        im = Image.open(p).convert("RGB")
    except Exception:
        return None
    return im if im.size == (800, 600) else None


def ink(r, g, b):
    return ((r > 170 and g > 150 and b < 130)
            or (r > 140 and g > 170 and b > 190)
            or (r > 170 and g < 130 and b < 130))


def cells(im, box):
    """返回 [(x0,x1,rows)] 逐字形；rows 为 '#'/.' 字符串。"""
    c = im.crop(box)
    w, h = c.size
    px = c.load()
    colink = [any(ink(*px[x, y]) for y in range(h)) for x in range(w)]
    out = []
    x = 0
    while x < w:
        if colink[x]:
            x0 = x
            while x < w and colink[x]:
                x += 1
            rows = []
            for y in range(h):
                rows.append("".join("#" if ink(*px[xx, y]) else "."
                                    for xx in range(x0, x)))
            while rows and "#" not in rows[0]:
                rows = rows[1:]
            while rows and "#" not in rows[-1]:
                rows = rows[:-1]
            out.append((x0 + box[0], x - 1 + box[0], tuple(rows)))
        else:
            x += 1
    return out


def key(rows):
    return hashlib.sha256("|".join(rows).encode()).hexdigest()[:6]


TBOX = (478, 112, 534, 145)


def decode_time(im):
    cs = cells(im, (450, 112, 540, 145))
    s = ""
    for a, b, rows in cs:
        k = key(rows)
        if k in GLY:
            s += GLY[k]
        elif k in LABEL:
            continue
        else:
            s += "?"
    return s, [(a, b, k) for a, b, rows in cs for k in [key(rows)]]


print("=== 25 张末截图：解码出的时间字段 vs 本窗末帧号 ===")
print("%-20s %-3s %7s %11s %9s %8s %9s %8s" % (
    "trip", "w", "f1", "解码时间", "秒", "f1/秒", "f1/31.2", "|差|>1s"))
unknown = 0
rows_out = []
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_x.png"))):
    im = load(p)
    if im is None:
        continue
    trip = os.path.basename(os.path.dirname(p))
    win = os.path.basename(p).split("_")[1]
    jp = os.path.join(os.path.dirname(p), "measure_%s.json" % win)
    f1 = None
    if os.path.exists(jp):
        ed = json.load(open(jp, encoding="utf-8")).get("frame_edges") or []
        f1 = ed[-1][0] if ed else None
    ds, dbg = decode_time(im)
    if "?" in ds or ds.count(":") < 2:
        print("%-20s %-3s %7s %11s  (无时间字段/未解析 keys=%s)" % (
            trip, win, f1, ds, [k for _, _, k in dbg]))
        unknown += 1
        continue
    try:
        hh, mm, ss = [int(z) for z in ds.split(":")]
    except ValueError:
        print("%-20s %-3s %7s %11s  (解析失败)" % (trip, win, f1, ds))
        unknown += 1
        continue
    secs = hh * 3600 + mm * 60 + ss
    ratio = (f1 / secs) if (f1 and secs) else -1
    pred = (f1 / 31.2) if f1 else -1
    dev = abs(pred - secs)
    rows_out.append((trip, win, f1, ds, secs, ratio, pred, dev))
    print("%-20s %-3s %7s %11s %9d %8.2f %9.2f %8s" % (
        trip, win, f1, ds, secs, ratio, pred, "**是**" if dev > 1.0 else "否"))

print()
print("=== 汇总 ===")
if rows_out:
    inb = [r for r in rows_out if 29.9 <= (r[2] / r[4]) <= 31.4]
    print("  可解码 %d 张；隐含 fps 落在 29.9..31.4 者 %d 张" % (len(rows_out), len(inb)))
    out = [(r[0], r[1], r[2], r[4], r[2] / r[4]) for r in rows_out
           if not (29.9 <= (r[2] / r[4]) <= 31.4)]
    print("  落在该带外：%s" % [(a, b, "f=%d s=%d fps=%.2f" % (c, d, e)) for a, b, c, d, e in out])
    bad = [(r[0], r[1], r[2], r[4], abs(r[2] / 31.2 - r[4])) for r in rows_out
           if abs(r[2] / 31.2 - r[4]) > 1.0]
    print("  |帧/31.2 - 屏显秒| > 1.0s 者：%s" % [(a, b, "f=%d s=%d 差%.2fs" % (c, d, e)) for a, b, c, d, e in bad])
    print("  未能解出时间字段（无面板/非游戏）：%d 张" % unknown)

print()
print("=== l3_20261023r/w2 两行比分数字（逐字解码）===")
im = load(os.path.join(BASE, "l3_20261023r", "measure_w2_end_x.png"))
for y0, y1, tag in [(170, 200, "行1(玩家)"), (200, 235, "行2(AI)"), (145, 172, "表头")]:
    cs = cells(im, (300, y0, 630, y1))
    txt = []
    for a, b, rows in cs:
        k = key(rows)
        txt.append("%d-%d:%s" % (a, b, GLY.get(k, "k" + k)))
    print("  %s: %s" % (tag, " ".join(txt)))
