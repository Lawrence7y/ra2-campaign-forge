#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导航辅助：单击 client 坐标 -> 截图 -> 打印关键全局量。合成输入+只读内存。"""
import sys, os, time, ctypes
from PIL import ImageGrab
import w177_core as W
from w177_click import click_client, move_client, force_foreground, game_hwnd

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass
u32 = ctypes.windll.user32

def shot(tag, full=True, bbox=None):
    img = ImageGrab.grab(bbox=bbox, all_screens=False) if bbox else ImageGrab.grab(all_screens=False)
    p = os.path.join(EVID, tag + ".png")
    img.save(p)
    print("  shot ->", p, img.size)
    return p

def globals_read(pid):
    m = W.Mem(pid)
    g = W.globals_snapshot(m)
    m.close()
    return g

def main():
    tag = sys.argv[1]
    x = int(sys.argv[2]); y = int(sys.argv[3])
    btn = sys.argv[4] if len(sys.argv) > 4 else "left"
    pid = W.pid_of()
    if not pid:
        print("no gamemd"); return 2
    print("pid=%d click %s (%d,%d) before=%s" % (pid, btn, x, y, globals_read(pid)))
    ok, info = click_client(pid, x, y, btn, settle=0.5)
    print("  click ok=%s %s" % (ok, info))
    time.sleep(0.6)
    print("  after globals=%s" % globals_read(pid))
    shot(tag + "_full", full=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
