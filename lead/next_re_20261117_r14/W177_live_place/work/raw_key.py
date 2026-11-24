#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""裸键盘：假定游戏已前台，直接 keybd_event，不做置前台。"""
import argparse
import ctypes
import sys
import time
from ctypes import wintypes as wt

u32 = ctypes.windll.user32
u32.keybd_event.argtypes = [wt.BYTE, wt.BYTE, wt.DWORD, ctypes.c_size_t]
u32.GetForegroundWindow.restype = wt.HWND
KEYUP = 0x0002


def tap(vk, hold=0.06):
    u32.keybd_event(vk & 0xFF, 0, 0, 0)
    time.sleep(hold)
    u32.keybd_event(vk & 0xFF, 0, KEYUP, 0)
    time.sleep(0.08)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vks", nargs="+", help="VK 十进制或 0x 十六进制，按顺序 tap")
    ap.add_argument("--count", type=int, default=1)
    a = ap.parse_args()
    print("foreground=0x%X" % u32.GetForegroundWindow())
    for _ in range(a.count):
        for s in a.vks:
            tap(int(s, 0))
    print("tapped %s x%d" % (a.vks, a.count))
    return 0


if __name__ == "__main__":
    sys.exit(main())
