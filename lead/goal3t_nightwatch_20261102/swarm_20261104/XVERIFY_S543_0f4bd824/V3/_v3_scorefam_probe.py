# -*- coding: utf-8 -*-
"""V3 独立复算 #9：全仓 PNG 的「计分屏同带行数」普查。

不用 OCR、不用猜坐标。参考件 = archive_T34/w1（本件已目视确认为计分屏，
表头「玩家/摧毁数/损失数/建造数/分数」+ 右上「游戏:1 / 时间:00:00:10」）。

两张**不同趟**的计分屏之间，固定文字/装饰行相同、只有数据行不同：
实测 T34/w1 vs T40/w1 = 152/190 行逐像素相同。故取阈值 >=130 视为「计分屏族」。

关键问题：计分屏会不会出现在**开局导航段**（navsig_nav_*/navsig_burst）？
若会，则「见计分屏 ⇒ 对局已结束」这个推断本身不成立。
"""
import collections
import glob
import hashlib
import json
import os
import re
import time

from PIL import Image

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
X0, X1, Y0, Y1 = 85, 630, 100, 290
REFS = [("archive_T34", "measure_w1_end_x.png"), ("archive_T40", "measure_w1_end_x.png")]


def load(p):
    try:
        im = Image.open(p).convert("RGB")
    except Exception:
        return None
    return im if im.size == (800, 600) else None


def rowhashes(im):
    return [hashlib.sha256(im.crop((X0, y, X1, y + 1)).tobytes()).hexdigest()
            for y in range(Y0, Y1)]


refs = [rowhashes(load(os.path.join(BASE, t, n))) for t, n in REFS]
print("参考件之间同带行数：%d/190" % sum(1 for a, b in zip(refs[0], refs[1]) if a == b))
print()

rows = []
for p in glob.glob(os.path.join(BASE, "**", "*.png"), recursive=True):
    if os.path.getsize(p) < 2000:
        continue
    im = load(p)
    if im is None:
        continue
    rh = rowhashes(im)
    best = max(sum(1 for a, b in zip(rh, r) if a == b) for r in refs)
    rows.append((best, os.path.relpath(p, BASE), os.path.getmtime(p)))

rows.sort(reverse=True)
score_fam = [r for r in rows if r[0] >= 130]
print("=== 计分屏族（同带行数 >=130/190）共 %d 张 ===" % len(score_fam))


def kind(rel):
    b = os.path.basename(rel)
    if b.startswith("measure_w"):
        return "窗末取证 measure_end"
    if b.startswith("navsig_nav_"):
        return "开局导航 navsig_nav_*"
    if b.startswith("navsig_burst"):
        return "导航突发 navsig_burst"
    if b.startswith("frame_target"):
        return "目标帧 frame_target"
    if b.startswith("frame_early"):
        return "早期帧 frame_early"
    if b.startswith("hb"):
        return "心跳 hb"
    return "其它 " + b[:18]


cnt = collections.Counter()
for sc, rel, mt in score_fam:
    cnt[kind(rel)] += 1
for k, v in cnt.most_common():
    print("   %-32s %d 张" % (k, v))
print()
print("=== 明细（前 60，按同带行数降序）===")
for sc, rel, mt in score_fam[:60]:
    print("   %3d/190  %-58s %s  [%s]" % (
        sc, rel, time.strftime("%m-%d %H:%M:%S", time.localtime(mt)), kind(rel)))

print()
print("=== 反向：25 张窗末取证里，**不**在计分屏族的 ===")
endfam = [r for r in score_fam if r[1].startswith(("archive", "l1", "l3")) and "measure_w" in r[1]]
allend = [p for p in glob.glob(os.path.join(BASE, "*", "measure_w*_end_x.png"))]
inset = {r[1] for r in score_fam}
for p in sorted(allend):
    rel = os.path.relpath(p, BASE).replace("\\", "/")
    if rel.replace("/", "\\") not in {r[1] for r in score_fam}:
        im = load(p)
        rh = rowhashes(im)
        best = max(sum(1 for a, b in zip(rh, r) if a == b) for r in refs)
        print("   %-52s 同带 %d/190" % (rel, best))
