#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""裸点击：假定游戏已前台、下拉已展开。只 SetCursorPos + mouse_event，不置前台不校验。
用于下拉列表项选择（避免 force_foreground 使下拉失焦）。
坐标 = client 坐标（client_origin 通常为 0,0）。
"""
import argparse
import ctypes
import sys
import time
from ctypes import wintypes as wt

u32 = ctypes.windll.user32
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.mouse_event.argtypes = [wt.DWORD, wt.DWORD, wt.DWORD, wt.DWORD, ctypes.c_size_t]
u32.SetForegroundWindow.argtypes = [wt.HWND]
u32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
u32.GetForegroundWindow.restype = wt.HWND

LEFTDOWN, LEFTUP = 0x0002, 0x0004


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cx", type=int, required=True)
    ap.add_argument("--cy", type=int, required=True)
    ap.add_argument("--n", type=int, default=1, help="repeat clicks")
    a = ap.parse_args()
    try:
        u32.SetProcessDPIAware()
    except Exception:
        pass
    fg = u32.GetForegroundWindow()
    print("foreground=0x%X" % fg)
    for k in range(a.n):
        u32.SetCursorPos(a.cx, a.cy)
        time.sleep(0.20)
        u32.mouse_event(LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.08)
        u32.mouse_event(LEFTUP, 0, 0, 0, 0)
        print("clicked (%d,%d) #%d" % (a.cx, a.cy, k + 1))
        time.sleep(0.25)
    return 0


if __name__ == "__main__":
    sys.exit(main())
