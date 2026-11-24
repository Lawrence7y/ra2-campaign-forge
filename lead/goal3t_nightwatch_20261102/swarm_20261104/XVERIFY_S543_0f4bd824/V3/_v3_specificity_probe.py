# -*- coding: utf-8 -*-
"""V3 独立复算 #11：计分屏判据的**真实特异性**。

用「两张不同趟计分屏上逐像素相同的固定文字行段」(100..123,139..195,210..234,244..289)
作为签名，测：
  (a) 25 张窗末截图里谁命中；
  (b) 全仓 1942 张**非窗末** PNG 里谁命中（假阳性=判据不特异）；
  (c) 命中的对照件在**本趟时间线上的位置**（早于 measure_w0 = 开局前就有计分屏
      ⇒ 「见计分屏 ⇒ 对局已结束」被推翻）。
"""
import collections
import glob
import hashlib
import json
import os
import time

from PIL import Image

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
X0, X1 = 85, 630
SEG = [(100, 124), (139, 196), (210, 235), (244, 290)]
PANEL = (85, 108, 630, 275)


def load(p):
    try:
        im = Image.open(p).convert("RGB")
    except Exception:
        return None
    return im if im.size == (800, 600) else None


def bp(im):
    px = im.crop(PANEL).tobytes()
    n = len(px) // 3
    hit = 0
    for i in range(0, len(px), 3):
        r, g, b = px[i], px[i + 1], px[i + 2]
        if b > r + 18 and b > g + 10 and 40 <= b <= 190 and r < 150:
            hit += 1
    return hit / n if n else 0.0


def rowh(im, y):
    return hashlib.sha256(im.crop((X0, y, X1, y + 1)).tobytes()).hexdigest()


def sig(im):
    parts = []
    for a, b in SEG:
        parts.append("".join(rowh(im, y) for y in range(a, b)))
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]


ends = []
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_x.png"))):
    im = load(p)
    if im is not None:
        ends.append((p, im, sig(im), bp(im)))
gc = collections.defaultdict(list)
for p, im, s, q in ends:
    gc[s].append(p)
print("=== 窗末截图签名组 ===")
for s, v in sorted(gc.items(), key=lambda kv: -len(kv[1])):
    print("  sig=%s n=%d p=%.3f..%.3f  %s" % (
        s, len(v), min(bp(load(x)) for x in v), max(bp(load(x)) for x in v),
        [os.path.relpath(x, BASE) for x in v][:4] if len(v) <= 4 else "%d imgs" % len(v)))

big = max(gc, key=lambda k: len(gc[k]))
score_sigs = {s for s, v in gc.items() if len(v) >= 2}
print()
print("  被 >=2 张窗末图共享的签名：%s" % sorted(score_sigs))

print()
print("=== 全仓对照（非 measure_w）命中同一签名者 ===")
rows = []
for p in sorted(glob.glob(os.path.join(BASE, "**", "*.png"), recursive=True)):
    if "measure_w" in os.path.basename(p):
        continue
    im = load(p)
    if im is None:
        continue
    s = sig(im)
    if s in score_sigs:
        rows.append((p, s, bp(im)))
print("  命中 %d 张（对照总数约 1942）" % len(rows))
for p, s, q in rows:
    trip = os.path.basename(os.path.dirname(p))
    jp = os.path.join(os.path.dirname(p), "measure_w0.json")
    jt = os.path.getmtime(jp) if os.path.exists(jp) else None
    et = os.path.getmtime(p)
    rel = ("早于w0 %.1fs" % ((jt - et))) if jt else "(无 measure_w0)"
    print("      %-52s sig=%s p=%.3f %s %s" % (
        os.path.relpath(p, BASE), s, q, rel,
        "<< 开局前即命中" if jt and et < jt else ""))

print()
print("=== 判据 p>=0.30 的特异性（Leader 实际用的判据）===")
tp = [(p, bp(im)) for p, im, s, q in ends if q >= 0.30]
fp = []
tot = 0
for p in sorted(glob.glob(os.path.join(BASE, "**", "*.png"), recursive=True)):
    if "measure_w" in os.path.basename(p):
        continue
    im = load(p)
    if im is None:
        continue
    tot += 1
    if bp(im) >= 0.30:
        fp.append(p)
print("  真阳性（窗末且 p>=0.30）%d 张；假阳性（对照且 p>=0.30）%d / %d 张 = %.1f%%" % (
    len(tp), len(fp), tot, 100.0 * len(fp) / max(tot, 1)))
print("  ⇒ 单靠 p 判「计分屏」的假阳率极高，见/不见计分屏必须由固定文字签名决定。")
