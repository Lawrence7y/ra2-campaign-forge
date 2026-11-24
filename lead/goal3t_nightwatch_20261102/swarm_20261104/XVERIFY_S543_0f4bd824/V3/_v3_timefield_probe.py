# -*- coding: utf-8 -*-
"""V3 独立复算 #10：只取「时间」字段那几个字，做帧号->屏显的独立性检验。

先定位：在标题行 (85,112)-(630,152) 内按 x 直方图找亮黄字簇。
然后只哈希**右侧时间字段**的掩码，得到与背景无关的「屏显秒」等价类。
若 时间 == 帧/31.2，则等价类必须与 floor(f/31.2+0.5) 单调一致：
  - 同一等价类里的帧号，换算后应落在同一秒；
  - 换算后不同秒的帧号，必须落在不同等价类。
后者是**硬检验**：同秒不同类 = 模型错；不同秒同类 = 模型错。
"""
import collections
import glob
import hashlib
import json
import os

from PIL import Image

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
ROW = (85, 112, 630, 152)


def load(p):
    try:
        im = Image.open(p).convert("RGB")
    except Exception:
        return None
    return im if im.size == (800, 600) else None


def yellows(im, box=ROW):
    c = im.crop(box)
    w, h = c.size
    px = c.tobytes()
    pts = []
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 3
            r, g, b = px[i], px[i + 1], px[i + 2]
            if r > 170 and g > 150 and b < 130 and (r - b) > 70 and (g - b) > 40:
                pts.append((x + box[0], y + box[1]))
    return pts


# 定位时间字段：archive_T34/w1 目视确认屏显 00:00:10，取黄色簇
ref = load(os.path.join(BASE, "archive_T34", "measure_w1_end_x.png"))
pts = yellows(ref)
hist = collections.Counter(x for x, y in pts)
cols = sorted(hist)
print("黄色像素 x 簇（archive_T34/w1，绝对坐标）：")
runs = []
for x in cols:
    if runs and x - runs[-1][-1] <= 3:
        runs[-1].append(x)
    else:
        runs.append([x])
for rn in runs:
    print("   x %d..%d  像素 %d" % (rn[0], rn[-1], sum(hist[x] for x in rn)))

# 时间字段 = 最右侧那一簇（HH:MM:SS 数字）
TR = runs[-1]
X0, X1 = TR[0] - 60, TR[-1] + 8
print("\n时间字段窗口取 x %d..%d（最后簇 %d..%d 外扩）" % (X0, X1, TR[0], TR[-1]))
BOX = (X0, ROW[1], X1, ROW[3])


def tsig(im):
    pts = sorted(yellows(im, BOX))
    return hashlib.sha256(str(pts).encode()).hexdigest()[:10], len(pts)


recs = []
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
    s, n = tsig(im)
    recs.append((trip, win, f1, s, n))

g = collections.defaultdict(list)
for trip, win, f1, s, n in recs:
    g[s].append((trip, win, f1, n))

print("\n=== 时间字段等价类（黄像素 <400 者视为无计分屏时间字段）===")
for s, v in sorted(g.items(), key=lambda kv: -len(kv[1])):
    ns = [x for x in v if x[3] >= 400]
    if not ns:
        print("  sig=%s n=%d 全部黄像素<400（非计分屏）: %s" % (
            s, len(v), [x[0] + "/w" + x[1][1] for x in v]))
        continue
    fs = sorted(x[2] for x in ns)
    lo, hi = fs[0] / 31.2, fs[-1] / 31.2
    ok = int(lo + 0.5) == int(hi + 0.5)
    print("  sig=%s n=%d 帧=%s -> /31.2 = %.2f..%.2f 秒 同秒?%s  %s" % (
        s, len(ns), fs, lo, hi, "YES" if ok else "**NO 冲突**",
        [x[0] + "/w" + x[1][1] for x in ns]))

print("\n=== 硬冲突清单：不同秒却同类 ===")
for s, v in g.items():
    fs = sorted(x[2] for x in v if x[3] >= 400 and x[2] is not None)
    if len(fs) > 1 and int(fs[0] / 31.2 + .5) != int(fs[-1] / 31.2 + .5):
        print("  sig=%s 帧 %s -> %.1fs vs %.1fs  成员 %s" % (
            s, fs, fs[0] / 31.2, fs[-1] / 31.2,
            ["%s/w%s" % (t, w) for t, w, f, ss, n in v if f is not None]))

print("\n=== 反向：同类同秒的一致性比例 ===")
tot = same = 0
for s, v in g.items():
    ns = [x for x in v if x[3] >= 400]
    for a in range(len(ns)):
        for b in range(a + 1, len(ns)):
            tot += 1
            if int(ns[a][2] / 31.2 + .5) == int(ns[b][2] / 31.2 + .5):
                same += 1
print("  同类等价对 %d，其中帧换算同秒 %d（%.1f%%）" % (tot, same, 100.0 * same / tot if tot else 0))

print("\n=== 每图明细 ===")
for trip, win, f1, s, n in sorted(recs, key=lambda r: (r[2] is None, r[2])):
    pred = ("%.2fs" % (f1 / 31.2)) if f1 is not None else "-"
    print("  %-18s w%s f1=%-6s %-8s 黄=%-4d  sig=%s" % (trip, win[-1], f1, pred, n, s))
