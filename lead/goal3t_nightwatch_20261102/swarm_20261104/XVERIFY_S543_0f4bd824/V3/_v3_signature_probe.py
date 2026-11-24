# -*- coding: utf-8 -*-
"""V3 独立复算 #4：从 20 张 p>=0.30 末截图里**反解**出「计分屏签名行」，
再用该签名对全仓 1942 张对照 PNG 做命中率检验（分离度）。

不猜坐标、不用 OCR。签名 = 在全部候选上都逐像素相同的 y 行集合。
"""
import collections
import glob
import hashlib
import os

from PIL import Image

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
X0, X1 = 85, 630
Y0, Y1 = 100, 290
PANEL = (85, 108, 630, 275)


def load(p):
    try:
        im = Image.open(p).convert("RGB")
    except Exception:
        return None
    return im if im.size == (800, 600) else None


def bp(im):
    px = im.crop(PANEL).tobytes()
    hit = 0
    n = len(px) // 3
    for i in range(0, len(px), 3):
        r, g, b = px[i], px[i + 1], px[i + 2]
        if b > r + 18 and b > g + 10 and 40 <= b <= 190 and r < 150:
            hit += 1
    return hit / n if n else 0.0


def rows(im):
    return [hashlib.sha256(im.crop((X0, y, X1, y + 1)).tobytes()).hexdigest()
            for y in range(Y0, Y1)]


cands = []
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png"))):
    im = load(p)
    if im is None:
        continue
    if bp(im) >= 0.30:
        cands.append((os.path.relpath(p, BASE), im, rows(im)))
print("p>=0.30 候选 %d 张" % len(cands))

# 逐行：在候选中「相同组大小 >= m」的行
common = []
for i in range(Y1 - Y0):
    vals = collections.Counter(r[i] for _, _, r in cands)
    top = vals.most_common(1)[0][1]
    common.append(top)
print()
print("=== 每行在 %d 张候选中的最大同值组大小（>=18 视为签名行）===" % len(cands))
sig = [Y0 + i for i, c in enumerate(common) if c >= 18]
for i, c in enumerate(common):
    if c >= 12:
        print("   y=%-4d 同值 %d/%d %s" % (Y0 + i, c, len(cands), "<= SIG" if c >= 18 else ""))
print("  签名行共 %d 行：%s" % (len(sig), (sig[:6], sig[-6:]) if sig else sig))

if sig:
    def sign(im):
        rr = rows(im)
        return hashlib.sha256("".join(rr[y - Y0] for y in sig).encode()).hexdigest()[:12]

    print()
    print("=== 候选上的签名 ===")
    gc = collections.defaultdict(list)
    for name, im, _ in cands:
        s = sign(im)
        gc[s].append(name)
    for k, v in sorted(gc.items(), key=lambda kv: -len(kv[1])):
        print("   sig=%s n=%d %s" % (k, len(v), v if len(v) <= 7 else "(%d)" % len(v)))

    print()
    print("=== 对照：全仓非 measure_w PNG 的签名命中 ===")
    allhits = collections.defaultdict(list)
    tot = 0
    for p in sorted(glob.glob(os.path.join(BASE, "**", "*.png"), recursive=True)):
        if "measure_w" in os.path.basename(p):
            continue
        im = load(p)
        if im is None:
            continue
        tot += 1
        allhits[sign(im)].append(os.path.relpath(p, BASE))
    print("  对照 PNG %d 张，签名组 %d 个" % (tot, len(allhits)))
    for k in gc:
        v = allhits.get(k, [])
        print("  候选签名 %s（候选 %d 张）-> 对照命中 %d 张: %s" % (
            k, len(gc[k]), len(v), v[:8]))
    print()
    print("  对照件里 p>=0.30 的张数：%d / %d" % (
        sum(1 for p in glob.glob(os.path.join(BASE, "**", "*.png"), recursive=True)
            if "measure_w" not in os.path.basename(p) and load(p) is not None
            and bp(load(p)) >= 0.30), tot))
