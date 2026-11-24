#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描屏幕候选点的放置光标颜色（红圈=拒绝 / 绿框=可放），在 ghost 激活后使用。
不写进程内存；仅移动鼠标 + ImageGrab 只读截图。避开侧栏边缘以防 auto-scroll。"""
import argparse
import ctypes
import os
import sys
import time
from PIL import ImageGrab
import w177_core as W
from w177_click import move_client, force_foreground, game_hwnd

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass


def colors(img, sx, sy, rad=70):
    im = img.convert("RGB"); px = im.load(); w, h = im.size
    red = green = 0
    redpts = []
    for y in range(max(0, sy - rad), min(h, sy + rad)):
        for x in range(max(0, sx - rad), min(w, sx + rad)):
            r, g, b = px[x, y]
            if r > 150 and g < 90 and b < 90:
                red += 1
                if len(redpts) < 8:
                    redpts.append((x, y))
            if g > 140 and r < 120 and b < 120:
                green += 1
    return red, green


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pts", required=True, help="semicolon separated X,Y points")
    ap.add_argument("--tag", default="sweep")
    ap.add_argument("--settle", type=float, default=0.22)
    ap.add_argument("--save-all", action="store_true")
    a = ap.parse_args()
    pid = W.pid_of()
    pts = []
    for p in a.pts.split(";"):
        if not p.strip():
            continue
        x, y = [int(v) for v in p.split(",")]
        pts.append((x, y))
    results = []
    for i, (x, y) in enumerate(pts):
        move_client(pid, x, y)
        time.sleep(a.settle)
        force_foreground(game_hwnd(pid))
        time.sleep(0.08)
        img = ImageGrab.grab(all_screens=False)
        red, green = colors(img, x, y)
        rec = {"i": i, "xy": [x, y], "red": red, "green": green}
        results.append(rec)
        if a.save_all or red > 30 or green > 30:
            img.save(os.path.join(EVID, "%s_%02d_%d_%d.png" % (a.tag, i, x, y)))
        print(json_line(rec))
    with open(os.path.join(EVID, a.tag + ".json"), "w", encoding="utf-8") as f:
        import json
        json.dump(results, f, ensure_ascii=False, indent=2)
    return 0


def json_line(rec):
    import json
    return json.dumps(rec)


if __name__ == "__main__":
    sys.exit(main())
