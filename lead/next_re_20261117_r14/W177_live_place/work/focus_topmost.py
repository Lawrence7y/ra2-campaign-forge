#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把游戏窗口设为 TOPMOST 并置前台，压过抢焦点的浏览器窗口。
用法：focus_topmost.py            -> 置顶
      focus_topmost.py --restore  -> 取消置顶
"""
import argparse
import ctypes
import subprocess
import sys
import time
from ctypes import wintypes as wt

u32 = ctypes.windll.user32
u32.SetWindowPos.argtypes = [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int,
                             ctypes.c_int, ctypes.c_int, wt.UINT]
u32.BringWindowToTop.argtypes = [wt.HWND]
u32.SetForegroundWindow.argtypes = [wt.HWND]
u32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
u32.GetForegroundWindow.restype = wt.HWND
u32.GetWindowTextA.argtypes = [wt.HWND, ctypes.c_char_p, ctypes.c_int]
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]

HWND_TOPMOST = wt.HWND(-1)
HWND_NOTOPMOST = wt.HWND(-2)
SWP_NOMOVE, SWP_NOSIZE, SWP_SHOWWINDOW = 0x0002, 0x0001, 0x0040


def pid_of(name="gamemd"):
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-Process %s -ErrorAction SilentlyContinue).Id" % name],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


def game_hwnds(pid):
    found = []

    def cb(hwnd, lparam):
        t = wt.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(t))
        if t.value == pid:
            buf = ctypes.create_string_buffer(256)
            u32.GetWindowTextA(hwnd, buf, 256)
            found.append((hwnd, buf.value.decode("latin-1", "replace"), u32.IsWindowVisible(hwnd)))
        return True

    EP = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    u32.EnumWindows(EP(cb), 0)
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--restore", action="store_true")
    ap.add_argument("--pid", type=int, default=None)
    a = ap.parse_args()
    pid = a.pid or pid_of()
    if not pid:
        print("gamemd not running")
        return 2
    ws = game_hwnds(pid)
    print("foreground before=0x%X" % u32.GetForegroundWindow())
    for hwnd, title, vis in ws:
        if not vis:
            continue
        r = wt.RECT()
        u32.GetWindowRect(hwnd, ctypes.byref(r))
        print("hwnd=0x%X title=%r rect=(%d,%d,%d,%d)" %
              (hwnd, title, r.left, r.top, r.right, r.bottom))
        if a.restore:
            u32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
        else:
            u32.ShowWindow(hwnd, 9)
            u32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            u32.BringWindowToTop(hwnd)
            u32.SetForegroundWindow(hwnd)
    time.sleep(0.3)
    print("foreground after=0x%X" % u32.GetForegroundWindow())
    return 0


if __name__ == "__main__":
    sys.exit(main())
