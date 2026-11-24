# -*- coding: utf-8 -*-
"""V3 独立复算 #16：用**已验证的字形解码器**给全仓 2036 张 PNG 打「结算屏」标记，
再与「该趟是否有 df==0 冻结窗」做列联，检验 S543 的核心推断方向：

    结算屏 ⇒ 对局已结束。

若结算屏也大量出现在**没有冻结窗**的趟，说明它是这条测试流程的常驻画面，
「窗末见结算屏」就不能推出「该窗期间对局结束」——S543 的推断强度被高估。
"""
import collections
import glob
import hashlib
import json
import os

from PIL import Image

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")

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
}


def norm(rows):
    rows = [r for r in rows if "#" in r]
    if not rows:
        return None
    w = max(len(r) for r in rows)
    return [r.ljust(w, ".") for r in rows]


def classify(rows):
    rows = norm(rows)
    if rows is None:
        return None
    best, bs = None, -1.0
    for d, t in SHAPES.items():
        if len(t) != len(rows) or len(t[0]) != len(rows[0]):
            continue
        tot = inter = 0
        for a, b in zip(rows, t):
            for ca, cb in zip(a, b):
                if ca == "#" or cb == "#":
                    tot += 1
                    if ca == cb == "#":
                        inter += 1
        s = inter / tot if tot else 0
        if s > bs:
            bs, best = s, d
    return best if bs >= 0.92 else None


def decode_time(px, x0, x1, y0, y1):
    def isy(x, y):
        r, g, b = px[x, y]
        return r > 170 and g > 150 and b < 130 and (r - b) > 70 and (g - b) > 40
    cols = [x for x in range(x0, x1) if any(isy(x, y) for y in range(y0, y1))]
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
        w = b - a + 1
        if w <= 2:
            out += ":"
            continue
        rows = []
        for y in range(y0, y1):
            ln = "".join("#" if isy(xx, y) else "." for xx in range(a, b + 1))
            if "#" in ln:
                rows.append(ln)
        d = classify(rows)
        out += d if d else "?"
    return out


frozen_trips = set()
for p in glob.glob(os.path.join(BASE, "*", "measure_w*.json")):
    j = json.load(open(p, encoding="utf-8"))
    ed = j.get("frame_edges") or []
    if ed and ed[0][0] != 0 and ed[0][0] == ed[-1][0]:
        frozen_trips.add(os.path.basename(os.path.dirname(p)))
all_trips = set(os.path.basename(os.path.dirname(p))
               for p in glob.glob(os.path.join(BASE, "*", "measure_w*.json")))

tab = collections.defaultdict(lambda: dict(n=0, tf=0, names=[]))
for p in glob.glob(os.path.join(BASE, "**", "*.png"), recursive=True):
    if os.path.getsize(p) < 2000:
        continue
    try:
        im = Image.open(p).convert("RGB")
    except Exception:
        continue
    if im.size != (800, 600):
        continue
    trip = os.path.basename(os.path.dirname(p))
    b = os.path.basename(p)
    key = (trip, "measure_end" if b.startswith("measure_w") else
           ("navsig" if b.startswith("navsig") else
            ("frame_target" if b.startswith("frame_target") else "其它")))
    ds = decode_time(im.load(), 476, 536, 112, 145)
    ok = ds.count(":") >= 2 and "?" not in ds and len([c for c in ds if c != ":"]) == 8
    tab[key]["n"] += 1
    if ok:
        tab[key]["tf"] += 1
        tab[key]["names"].append((b, ds))

print("=== 解码器自检：窗末取证里解出的时间字段 ===")
for (trip, kind), v in sorted(tab.items()):
    if kind == "measure_end":
        print("  %-18s 图 %d 张，解出时间字段 %d 张  %s" % (
            trip, v["n"], v["tf"], [d for _, d in v["names"]]))

print()
print("=== 列联：结算屏(解出 HH:MM:SS) 出现率，按「该趟有无 df==0 冻结窗」× 图类别 ===")
for kind in ("measure_end", "navsig", "frame_target", "其它"):
    a = b = c = d = 0
    for (trip, k), v in tab.items():
        if k != kind:
            continue
        hasf = trip in frozen_trips
        if hasf and v["tf"]:
            a += 1
        elif hasf and not v["tf"]:
            b += 1
        elif not hasf and v["tf"]:
            c += 1
        else:
            d += 1
    print("  %-13s 有冻结窗&见时间字段 %-3d | 有冻结窗&未见 %-3d | 无冻结窗&见 %-3d | 无冻结窗&未见 %-3d"
          % (kind, a, b, c, d))

print()
print("=== 无冻结窗的趟里，哪些图解出了时间字段（这些是潜在反例）===")
n = 0
for (trip, kind), v in sorted(tab.items()):
    if trip in frozen_trips or not v["tf"]:
        continue
    print("  %-18s %-13s %s" % (trip, kind, v["names"]))
    n += 1
print("  共 %d 个 (趟,类别) 组合" % n)
