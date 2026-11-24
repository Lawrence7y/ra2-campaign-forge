#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""先置游戏前台，再抓屏（避免 harness 窗口遮挡）。只读屏幕 + 前台切换。"""
import argparse, ctypes, os, time
from PIL import ImageGrab
import w177_core as W
from w177_click import game_hwnd, force_foreground

try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

EVID = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-D\EVIDENCE"

ap = argparse.ArgumentParser()
ap.add_argument("--tag", required=True)
ap.add_argument("--bbox", default=None)
ap.add_argument("--full", action="store_true")
a = ap.parse_args()

pid = W.pid_of()
if not pid:
    print("gamemd not running"); raise SystemExit(2)
hwnd = game_hwnd(pid)
ok = force_foreground(hwnd, settle=0.6) if hwnd else False
time.sleep(0.2)
if a.full:
    img = ImageGrab.grab(all_screens=False)
else:
    bbox = tuple(int(x) for x in a.bbox.split(",")) if a.bbox else (0, 0, 800, 600)
    img = ImageGrab.grab(bbox=bbox, all_screens=False)
path = os.path.join(EVID, a.tag + ".png")
img.save(path)
m = W.Mem(pid)
print("fg=%s hwnd=%s frame=%s mode=%s saved=%s size=%s" %
      (ok, hex(hwnd) if hwnd else None, m.u32(W.A_FRAME), m.u32(W.A_MODE), path, img.size))
