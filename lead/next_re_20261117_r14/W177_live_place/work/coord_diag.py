#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""坐标诊断：DPI 缩放、屏幕物理尺寸、游戏窗口 rect / client origin（DPI-aware 视角）。"""
import ctypes
import subprocess
from ctypes import wintypes as wt
from PIL import ImageGrab

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
u32.SetProcessDPIAware()
u32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u32.GetClientRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u32.ClientToScreen.argtypes = [wt.HWND, ctypes.POINTER(wt.POINT)]
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]


def pid_of():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-Process gamemd -ErrorAction SilentlyContinue).Id"],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


def main():
    img = ImageGrab.grab(all_screens=False)
    print("screen physical = %dx%d" % img.size)
    print("(GetSystemMetrics) CX=%d CY=%d" % (u32.GetSystemMetrics(0), u32.GetSystemMetrics(1)))
    hdc = u32.GetDC(0)
    print("LOGPIXELSX=%d (96=100%%, 144=150%%)" % u32.GetDeviceCaps(hdc, 88))
    u32.ReleaseDC(0, hdc)
    pid = pid_of()
    hwnds = []

    def cb(hwnd, lp):
        t = wt.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(t))
        if t.value == pid and u32.IsWindowVisible(hwnd):
            hwnds.append(hwnd)
        return True

    EP = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    u32.EnumWindows(EP(cb), 0)
    import os
    os.environ['__dummy'] = '1'
    for hwnd in hwnds:
        r = wt.RECT()
        cl = wt.RECT()
        pt = wt.POINT(0, 0)
        u32.GetWindowRect(hwnd, ctypes.byref(r))
        u32.GetClientRect(hwnd, ctypes.byref(cl))
        u32.ClientToScreen(hwnd, ctypes.byref(pt))
        print("hwnd=0x%X win=(%d,%d,%d,%d) client=%dx%d client_origin=(%d,%d)" % (
            hwnd, r.left, r.top, r.right, r.bottom,
            cl.right - cl.left, cl.bottom - cl.top, pt.x, pt.y))
    return 0


if __name__ == "__main__":
    main()
