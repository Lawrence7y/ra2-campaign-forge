#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""真实建造放置点击：移动->充分等待渲染->按下保持->抬起。用于 NAPOWR 放置。"""
import argparse
import ctypes
import subprocess
import sys
import time
from ctypes import wintypes as wt

u32 = ctypes.windll.user32
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.mouse_event.argtypes = [wt.DWORD, wt.DWORD, wt.DWORD, wt.DWORD, ctypes.c_size_t]
u32.SetForegroundWindow.argtypes = [wt.HWND]
u32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
u32.GetForegroundWindow.restype = wt.HWND
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]

LEFTDOWN, LEFTUP = 0x0002, 0x0004


def pid_of():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-Process gamemd -ErrorAction SilentlyContinue).Id"],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


def game_hwnd(pid):
    found = []

    def cb(hwnd, lp):
        t = wt.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(t))
        if t.value == pid and u32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True

    EP = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    u32.EnumWindows(EP(cb), 0)
    return found[0] if found else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cx", type=int, required=True)
    ap.add_argument("--cy", type=int, required=True)
    ap.add_argument("--mode-enter", action="store_true", help="先点建造栏格子(2340,467)进入建造模式")
    ap.add_argument("--hold", type=float, default=0.30)
    a = ap.parse_args()
    try:
        u32.SetProcessDPIAware()
    except Exception:
        pass
    pid = pid_of()
    hwnd = game_hwnd(pid) if pid else None
    if hwnd:
        u32.SetForegroundWindow(hwnd)
        time.sleep(0.2)
    if a.mode_enter:
        u32.SetCursorPos(2340, 467)
        time.sleep(0.25)
        u32.mouse_event(LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.10)
        u32.mouse_event(LEFTUP, 0, 0, 0, 0)
        time.sleep(0.5)
        print("entered build mode at build slot")
    # 移动到目标，充分等待虚影渲染
    u32.SetCursorPos(a.cx, a.cy)
    time.sleep(1.0)
    # 轻微抖动确保 WM_MOUSEMOVE
    u32.SetCursorPos(a.cx + 2, a.cy + 2)
    time.sleep(0.15)
    u32.SetCursorPos(a.cx, a.cy)
    time.sleep(0.6)
    u32.mouse_event(LEFTDOWN, 0, 0, 0, 0)
    time.sleep(a.hold)
    u32.mouse_event(LEFTUP, 0, 0, 0, 0)
    time.sleep(0.5)
    print("placed click at (%d,%d) hold=%.2f" % (a.cx, a.cy, a.hold))
    return 0


if __name__ == "__main__":
    sys.exit(main())
