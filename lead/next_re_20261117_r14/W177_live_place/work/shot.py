#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""屏幕截图（只读屏幕，不触碰目标进程内存）。DPI-aware，抓左上 800x600 或全屏。
用 PIL.ImageGrab。输出 PNG 到 EVIDENCE/。
"""
import argparse
import os
import sys
import time

from PIL import ImageGrab

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")

try:
    import ctypes
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--bbox", default="0,0,800,600")
    ap.add_argument("--full", action="store_true", help="忽略 bbox，抓全屏并缩放到 1280x720")
    a = ap.parse_args()
    if a.full:
        img = ImageGrab.grab(all_screens=False)
        img.thumbnail((1280, 720))
    else:
        box = tuple(int(x) for x in a.bbox.split(","))
        img = ImageGrab.grab(bbox=box, all_screens=False)
    path = os.path.join(EVID, a.tag + ".png")
    img.save(path)
    print("saved=%s size=%s" % (path, img.size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
