# -*- coding: utf-8 -*-
"""V3 独立复算 #2：计分屏判据的**分离度**检验。

S543 §七.7 自己承认「像素判据 p 单独不足以判定计分屏」，蓝紫加载/简报屏也能
p≈0.40。本件用两条**不依赖读数**的客观判据重做分离：

  K1 = 表头带像素指纹：计分屏的「玩家/摧毁数/损失数/建造数/分数」表头行是
       **位图字，内容固定**，任何计分屏在该带上应逐像素相同。
  K2 = 「时间」标签位（不含数字）指纹：同样固定。
  对照 = 同目录其它 PNG（frame_target_01 / hb / nav 等）。
"""
import collections
import glob
import hashlib
import json
import os

from PIL import Image

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
PANEL = (85, 108, 630, 275)
HDR = (85, 130, 630, 152)     # 表头带（在时间行之下、数据行之上）
TIMER = (430, 118, 640, 150)


def bp(im, box=PANEL):
    px = im.crop(box).tobytes()
    n = len(px) // 3
    hit = 0
    for i in range(0, len(px), 3):
        r, g, b = px[i], px[i + 1], px[i + 2]
        if b > r + 18 and b > g + 10 and 40 <= b <= 190 and r < 150:
            hit += 1
    return hit / n if n else 0.0


def h(im, box):
    return hashlib.sha256(im.crop(box).tobytes()).hexdigest()[:10]


def load(p):
    try:
        im = Image.open(p).convert("RGB")
    except Exception:
        return None
    return im if im.size == (800, 600) else None


recs = []
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png"))):
    im = load(p)
    if im is None:
        continue
    recs.append(dict(tag="ENDPNG", trip=os.path.basename(os.path.dirname(p)),
                     name=os.path.basename(p), p=bp(im),
                     hdr=h(im, HDR), tmr=h(im, TIMER),
                     f1=None, path=p))

print("=== A. 25 张末截图：p + 表头带指纹 + 计时器带指纹 ===")
for r in recs:
    print("  %-18s %-26s p=%.4f hdr=%s tmr=%s" % (
        r["trip"], r["name"], r["p"], r["hdr"], r["tmr"]))
gh = collections.defaultdict(list)
for r in recs:
    gh[r["hdr"]].append(r["trip"] + "/" + r["name"])
print()
print("  表头带指纹组：%d 组 / %d 张" % (len(gh), len(recs)))
for k, v in sorted(gh.items(), key=lambda kv: -len(kv[1])):
    print("    hdr=%s n=%d  %s" % (k, len(v), v if len(v) < 8 else "%d imgs" % len(v)))

print()
print("=== B. 对照组：各趟其它 PNG 的同判据 ===")
others = []
for p in sorted(glob.glob(os.path.join(BASE, "*", "*.png"))):
    if "measure_w" in os.path.basename(p):
        continue
    im = load(p)
    if im is None:
        continue
    others.append(dict(trip=os.path.basename(os.path.dirname(p)),
                       name=os.path.basename(p), p=bp(im), hdr=h(im, HDR),
                       tmr=h(im, TIMER)))
kind = collections.Counter()
for o in others:
    kind[o["hdr"]] += 1
print("  对照 PNG 共 %d 张，表头带指纹组 %d 个" % (len(others), len(kind)))
endhdr = set(r["hdr"] for r in recs if r["p"] >= 0.30)
match = [o for o in others if o["hdr"] in endhdr]
print("  ★ 表头带与「p>=0.30 末截图」完全相同的对照件：%d 张" % len(match))
for o in match:
    print("      %s/%s p=%.4f" % (o["trip"], o["name"], o["p"]))
print()
print("  对照件 p 分布抽样（前 25）：")
for o in others[:25]:
    print("      %-18s %-24s p=%.4f hdr=%s" % (o["trip"], o["name"], o["p"], o["hdr"]))

print()
print("=== C. 分离度汇总 ===")
hi = [r["p"] for r in recs if r["hdr"] in endhdr]
lo = [r["p"] for r in others if r["hdr"] not in endhdr]
print("  末截图共享同一表头带者 n=%d，其 p 范围 %.4f..%.4f" % (
    len(hi), min(hi), max(hi)) if hi else "  none")
if lo:
    print("  未命中该表头带的对照件 %d 张，p 范围 %.4f..%.4f，p>=0.30 者 %d 张" % (
        len(lo), min(lo), max(lo), sum(1 for x in lo if x >= 0.30)))
print()
print("  ★ 判据 K1（表头带逐像素相同）在末截图上命中 %d/25；"
      "对照 PNG 上误报 %d/%d" % (len(hi), len(match), len(others)))
