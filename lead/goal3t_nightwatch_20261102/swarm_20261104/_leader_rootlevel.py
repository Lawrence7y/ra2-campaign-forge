# -*- coding: utf-8 -*-
"""§543 补丁：把根目录层级的 measure_w*.json / png 也纳入普查（T55h/T55j）。

§543 首版只扫了 `*/measure_w*.json`（单层子目录），漏掉 qc161_u0400_trip 根下的
3 份 json 与 2 张 end 截图。本件补全，并在台账登记该口径缺口。

判据与 §543 完全一致，便于合并。
"""
import glob
import hashlib
import json
import os

from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
PANEL = (85, 108, 630, 275)


def panel_p(im):
    c = im.convert("RGB").crop(PANEL)
    px = list(c.getdata())
    n = len(px)
    hit = sum(1 for r, g, b in px if b > r + 18 and b > g + 10 and 40 <= b <= 190 and r < 150)
    return hit / n if n else 0.0


print("=== 根目录层级 measure_w*.json（此前漏扫）===")
for p in sorted(glob.glob(os.path.join(BASE, "measure_w*.json"))):
    j = json.load(open(p, encoding="utf-8"))
    ed = j.get("frame_edges") or []
    f0 = ed[0][0] if ed else None
    f1 = ed[-1][0] if ed else None
    df = (f1 - f0) if ed else None
    print("  %-16s trip=%-18s w=%s edges=%d f=[%s,%s] df=%s span=%s verdict=%s" % (
        os.path.basename(p), j.get("trip_id"), j.get("window"), len(ed),
        f0, f1, df, j.get("span_s"), j.get("verdict")))
    # 同窗 end 截图
    png = os.path.join(BASE, "measure_w%s_end_x.png" % j.get("window"))
    if os.path.exists(png):
        im = Image.open(png)
        im.load()
        ph = hashlib.sha256(im.convert("RGB").tobytes()).hexdigest()[:16]
        print("       end_x: p=%.3f  pixhash=%s" % (panel_p(im), ph))
    else:
        print("       end_x: 无")

print()
print("=== 口径澄清：§543 首版扫的是 */measure_w*.json（单层子目录）===")
sub = glob.glob(os.path.join(BASE, "*", "measure_w*.json"))
print("  子目录 json: %d 份" % len(sub))
print("  根目录 json: %d 份" % len(glob.glob(os.path.join(BASE, "measure_w*.json"))))
print("  合计: %d 份" % (len(sub) + len(glob.glob(os.path.join(BASE, "measure_w*.json")))))
print()
print("  子目录 end_png: %d 张" % len(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png"))))
print("  根目录 end_png: %d 张" % len(glob.glob(os.path.join(BASE, "measure_w*_end_*.png"))))
print("  合计: %d 张" % (len(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png")))
                          + len(glob.glob(os.path.join(BASE, "measure_w*_end_*.png")))))
