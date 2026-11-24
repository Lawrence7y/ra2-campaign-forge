# -*- coding: utf-8 -*-
"""V3 独立复算 #17：全仓 PNG 的「时间字段」精确普查（哈希级，非肉眼）。

已验证的字形行哈希（黄字点阵，窗口 x[478,534) y[112,145)）：
  0 -> 1f997d   1 -> 1c95e5   2 -> 83c50a   3 -> f9dfba   4 -> 28b1bf
  5 -> 52af2d   6 -> 41fd3c   8 -> 94ea9d   9 -> 49d82d
这些哈希由 9 个**互相独立**的读数反推（00:00:10/15/24/28/29/30/31/32、00:02:56），
彼此自洽：同一形状在不同趟出现、且换算成同一个秒数。

按「该图的 8 个数字位全部命中模板」判定 = 该图上有 HH:MM:SS。
再按图类别与「本趟是否有冻结窗」列联，检验「见结算屏 ⇒ 对局已结束」的方向性。
"""
import collections
import glob
import hashlib
import json
import os

from PIL import Image

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
X0, X1, Y0, Y1 = 478, 534, 112, 145
GLY = {"1f997d": "0", "1c95e5": "1", "83c50a": "2", "f9dfba": "3",
       "28b1bf": "4", "52af2d": "5", "41fd3c": "6", "94ea9d": "8",
       "49d82d": "9"}


def kh(rows):
    return hashlib.sha256("|".join(rows).encode()).hexdigest()[:6]


def decode(im):
    px = im.load()

    def isy(x, y):
        r, g, b = px[x, y]
        return r > 170 and g > 150 and b < 130 and (r - b) > 70 and (g - b) > 40
    cols = [x for x in range(X0, X1) if any(isy(x, y) for y in range(Y0, Y1))]
    if not cols:
        return ""
    segs = []
    prev = None
    for x in cols:
        if prev is None or x - prev > 1:
            segs.append([x, x])
        else:
            segs[-1][1] = x
        prev = x
    out = ""
    for a, b in segs:
        if b - a + 1 <= 2:
            out += ":"
            continue
        rows = []
        for y in range(Y0, Y1):
            ln = "".join("#" if isy(xx, y) else "." for xx in range(a, b + 1))
            if "#" in ln:
                rows.append(ln)
        out += GLY.get(kh(rows), "?")
    return out


def is_hms(ds):
    dg = [c for c in ds if c != ":"]
    return len(dg) == 8 and "?" not in dg


frozen = set()
for p in glob.glob(os.path.join(BASE, "*", "measure_w*.json")):
    j = json.load(open(p, encoding="utf-8"))
    ed = j.get("frame_edges") or []
    if ed and ed[0][0] != 0 and ed[0][0] == ed[-1][0]:
        frozen.add(os.path.basename(os.path.dirname(p)))

cat = collections.Counter()
hit = collections.Counter()
hits_by_trip = collections.defaultdict(list)
bad = 0
for p in glob.glob(os.path.join(BASE, "**", "*.png"), recursive=True):
    if os.path.getsize(p) < 2000:
        continue
    try:
        im = Image.open(p).convert("RGB")
    except Exception:
        continue
    if im.size != (800, 600):
        continue
    b = os.path.basename(p)
    trip = os.path.basename(os.path.dirname(p))
    k = ("A 窗末取证" if b.startswith("measure_w") else
         "B navsig_burst" if b.startswith("navsig_burst") else
         "C navsig_nav_*" if b.startswith("navsig_nav") else
         "D frame_target_*" if b.startswith("frame_target") else
         "E frame_early_*" if b.startswith("frame_early") else
         "F spot_*" if b.startswith("spot") else "G 其它")
    cat[k] += 1
    ds = decode(im)
    if is_hms(ds):
        hit[k] += 1
        hits_by_trip[trip].append((k, b, ds))
    elif ds.count(":") >= 2 and ds:
        bad += 1

print("=== 全仓 800x600 PNG 的 HH:MM:SS 命中（哈希级判定）===")
print("%-18s %8s %10s" % ("类别", "张数", "含时分秒"))
for k in sorted(cat):
    print("%-18s %8d %10d" % (k, cat[k], hit[k]))
print("（另有 %d 张解出 >=2 个冒号但数字位未全命中模板 = 部分/异字体）" % bad)

print()
print("=== 命中图按趟汇总，并标注该趟是否有 df==0 冻结窗 ===")
for t in sorted(hits_by_trip):
    print("  %-18s 冻结窗趟=%-5s  %s" % (t, t in frozen, hits_by_trip[t]))

print()
print("=== 关键反例检查：navsig_* / frame_* 这些**非窗末**图里出现时分秒的趟 ===")
for t in sorted(hits_by_trip):
    nonend = [x for x in hits_by_trip[t] if x[0] != "A 窗末取证"]
    if nonend:
        print("  %-18s %s" % (t, nonend))
