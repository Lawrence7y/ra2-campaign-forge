#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""屏幕截图（只读屏幕）。DPI-aware，写 PNG 到 W177-B/EVIDENCE/。"""
import argparse
import os
import sys

from PIL import ImageGrab

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")

try:
    import ctypes
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass


def save(tag, bbox=None, full=False, scale=None):
    if full:
        img = ImageGrab.grab(all_screens=False)
    else:
        img = ImageGrab.grab(bbox=bbox or (0, 0, 800, 600), all_screens=False)
    if scale:
        img.thumbnail(scale)
    path = os.path.join(EVID, tag + ".png")
    img.save(path)
    # 简单黑屏判定：统计非黑像素比例
    small = img.convert("RGB").resize((80, 60))
    nonblack = sum(1 for p in small.getdata() if max(p) > 24)
    return path, img.size, nonblack / (80 * 60)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--bbox", default=None)
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--max", default=None, help="e.g. 1280,720")
    a = ap.parse_args()
    bbox = tuple(int(x) for x in a.bbox.split(",")) if a.bbox else None
    scale = tuple(int(x) for x in a.max.split(",")) if a.max else None
    path, size, frac = save(a.tag, bbox, a.full, scale)
    print("saved=%s size=%s nonblack_frac=%.3f" % (path, size, frac))
    return 0


if __name__ == "__main__":
    sys.exit(main())
