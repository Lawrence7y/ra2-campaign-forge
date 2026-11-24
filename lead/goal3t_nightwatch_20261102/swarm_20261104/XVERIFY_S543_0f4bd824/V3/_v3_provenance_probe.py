# -*- coding: utf-8 -*-
"""V3 独立复算 #8：全仓 PNG 文件级重复 + 「png mtime 是否等于本趟 measure json mtime」。

若同一份字节出现在多个趟目录，且 mtime 不属于该趟，则该 png 不能当作
「该趟该窗的现场证据」。这是对 S543 全部 25 张证据的**出处有效性**检验。
"""
import collections
import glob
import hashlib
import json
import os
import time

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
TIMER = (430, 118, 640, 150)

from PIL import Image


def fsha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:10]


def tm(t):
    return time.strftime("%m-%d %H:%M:%S", time.localtime(t))


groups = collections.defaultdict(list)
n = 0
for p in glob.glob(os.path.join(BASE, "**", "*.png"), recursive=True):
    try:
        if os.path.getsize(p) < 2000:
            continue
    except OSError:
        continue
    n += 1
    groups[fsha(p)].append(p)

multi = {k: v for k, v in groups.items() if len({os.path.basename(os.path.dirname(x)) for x in v}) > 1}
print("扫描 PNG %d 张（>=2KB）；跨趟字节相同的重复组：%d 个" % (n, len(multi)))
tot = 0
for k, v in sorted(multi.items(), key=lambda kv: -len(kv[1]))[:14]:
    trips = collections.Counter(os.path.basename(os.path.dirname(x)) for x in v)
    tot += len(v)
    print("  sha=%s 共 %d 份，跨 %d 趟：" % (k, len(v), len(trips)))
    for x in sorted(v)[:9]:
        print("      %-56s %s" % (os.path.relpath(x, BASE), tm(os.path.getmtime(x))))
print("  （前 14 组涉及 %d 份文件）" % tot)

print()
print("=== measure_w*_end_x.png 的 mtime 与本趟 measure json / fields 的对账 ===")
print("%-20s %-3s %-12s %-12s %-12s %s" % ("trip", "w", "png_mtime", "json_mtime", "fields_mtime", "判定"))
bad = []
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_x.png"))):
    d = os.path.dirname(p)
    trip = os.path.basename(d)
    w = os.path.basename(p).split("_")[1]
    jp = os.path.join(d, "measure_%s.json" % w)
    fp = os.path.join(d, "qc151_fields.json")
    pt = os.path.getmtime(p)
    jt = os.path.getmtime(jp) if os.path.exists(jp) else None
    ft = os.path.getmtime(fp) if os.path.exists(fp) else None
    if jt is None:
        verdict = "无 json"
    elif abs(pt - jt) <= 2:
        verdict = "OK(=json)"
    else:
        verdict = "**错位 %+.0fs**" % (pt - jt)
        bad.append((trip, w, pt - jt))
    # fields 里该窗的 forensics 是否声明写了这个 png
    declared = "?"
    if os.path.exists(fp):
        for r in json.load(open(fp, encoding="utf-8")):
            v = r.get("value")
            if (r.get("group") == "MEASURE" and isinstance(v, dict)
                    and "empty_window" in v and v.get("window") == int(w[-1])):
                declared = ("declared=%s empty=%s" % (
                    bool(v.get("forensics_png")), v.get("empty_window")))
    print("%-20s %-3s %-12s %-12s %-12s %-16s %s" % (
        trip, w, tm(pt), tm(jt) if jt else "-", tm(ft) if ft else "-", verdict, declared))

print()
print("=== 同趟 fields 里所有 PNG 与本 png 字节相同者（找出处）===")
src = collections.defaultdict(list)
for p in glob.glob(os.path.join(BASE, "**", "*.png"), recursive=True):
    if os.path.getsize(p) > 2000:
        src[fsha(p)].append(p)
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_x.png"))):
    trip = os.path.basename(os.path.dirname(p))
    w = os.path.basename(p).split("_")[1]
    same = [os.path.relpath(x, BASE) for x in src[fsha(p)]]
    if len(same) > 1:
        print("  %s/w%s -> 同字节文件 %d 份: %s" % (trip, w, len(same), same[:8]))
