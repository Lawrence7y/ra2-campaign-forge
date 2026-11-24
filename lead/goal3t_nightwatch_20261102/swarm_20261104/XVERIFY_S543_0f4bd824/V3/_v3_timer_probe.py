# -*- coding: utf-8 -*-
"""V3 独立复算 #1：末截图「计时器」区域的像素指纹分组 + 帧号单调性检验。

只读。零真机。判据不依赖 OCR，也不依赖 Leader 的数字。

思路：
  RA2 遭遇战得分屏的「时间」字段是 HH:MM:SS 位图字。若「时间 = 帧号/31.2」成立，
  则 (a) 同一帧号的窗 -> 同一计时器像素指纹；
      (b) 帧号差异大到跨过 1 秒 -> 计时器像素指纹必须不同；
      (c) 帧号差异不足 1 秒 -> 允许相同。
  反过来，若两个**不同趟**（不同地图/不同单位）的整幅图逐字节相同，
  说明这些 png 不是各自趟的独立采集。
"""
import collections
import glob
import hashlib
import json
import os

from PIL import Image

BASE = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
        r"\CONTINUE_20261003\lead\qc161_u0400_trip")
TIMER = (430, 118, 640, 150)      # Leader 自己在 _leader_timer_w1w2.py:17 用的框
PANEL = (85, 108, 630, 275)

recs = []
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png"))):
    trip = os.path.basename(os.path.dirname(p))
    win = os.path.basename(p).split("_")[1]
    im = Image.open(p).convert("RGB")
    th = hashlib.sha256(im.crop(TIMER).tobytes()).hexdigest()[:10]
    ph = hashlib.sha256(im.tobytes()).hexdigest()[:10]
    fh = hashlib.sha256(open(p, "rb").read()).hexdigest()[:10]
    jp = os.path.join(os.path.dirname(p), "measure_%s.json" % win)
    f1 = None
    if os.path.exists(jp):
        j = json.load(open(jp, encoding="utf-8"))
        ed = j.get("frame_edges") or []
        f1 = ed[-1][0] if ed else None
    recs.append(dict(trip=trip, win=win, f1=f1, th=th, ph=ph, fh=fh,
                     mtime=os.path.getmtime(p)))

print("=== 1. 计时器区域像素指纹分组（%d 组 / %d 张）===" % (
    len({r["th"] for r in recs}), len(recs)))
g = collections.defaultdict(list)
for r in recs:
    g[r["th"]].append(r)
for th, v in sorted(g.items(), key=lambda kv: -len(kv[1])):
    print("  timer=%s n=%d  frames=%s  ->  %s" % (
        th, len(v), sorted(set(str(x["f1"]) for x in v)),
        ",".join("%s/%s" % (x["trip"], x["win"]) for x in v)))

print()
print("=== 2. 整幅 / 文件级 指纹重复组（跨趟相同 = 不是各自独立采集）===")
for key in ("ph", "fh"):
    gg = collections.defaultdict(list)
    for r in recs:
        gg[r[key]].append(r)
    for k, v in sorted(gg.items(), key=lambda kv: -len(kv[1])):
        if len(v) > 1:
            trips = sorted(set(x["trip"] for x in v))
            print("  %s=%s n=%d trips=%d %s" % (
                key, k, len(v), len(trips),
                " | ".join("%s/%s f1=%s mtime=%s" % (
                    x["trip"], x["win"], x["f1"],
                    __import__("time").strftime(
                        "%m-%d %H:%M:%S", __import__("time").localtime(x["mtime"])))
                    for x in v)))

print()
print("=== 3. 同趟 w1 vs w2：计时器区域是否逐像素相同 ===")
bt = collections.defaultdict(dict)
for r in recs:
    bt[r["trip"]][r["win"]] = r
n_same = n_diff = 0
for t in sorted(bt):
    d = bt[t]
    if "w1" in d and "w2" in d:
        same = d["w1"]["th"] == d["w2"]["th"]
        n_same += same
        n_diff += (not same)
        print("  %-18s f1(w1)=%-6s f1(w2)=%-6s TIMER_SAME=%-5s (%s vs %s)" % (
            t, d["w1"]["f1"], d["w2"]["f1"], same, d["w1"]["th"], d["w2"]["th"]))
print("  => 相同 %d / 不同 %d" % (n_same, n_diff))

print()
print("=== 4. 帧号 -> 计时器指纹 的单调性（同一 timer 组内帧号跨度）===")
for th, v in sorted(g.items()):
    fs = sorted(set(x["f1"] for x in v if x["f1"] is not None))
    if len(fs) > 1:
        print("  timer=%s 帧号集合 %s 跨度 %d -> 若 fps=31.2 则秒跨度 %.1fs" % (
            th, fs, fs[-1] - fs[0], (fs[-1] - fs[0]) / 31.2))

print()
print("=== 5. 各趟 f1 与 timer 指纹一表（供逐条核对）===")
for r in sorted(recs, key=lambda x: (x["f1"] if x["f1"] is not None else -1)):
    print("  f1=%-6s %-18s %-3s timer=%s full=%s" % (
        r["f1"], r["trip"], r["win"], r["th"], r["ph"]))
