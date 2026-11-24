#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合成键盘输入与鼠标滚轮。子命令：key <vk> [count] / keys <vk,vk,...> / wheel <delta> [cx cy]
VK 用十进制或 0x 十六进制；keybd_event 合成。
"""
import argparse
import ctypes
import sys
import time
from ctypes import wintypes as wt

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
u32.SetForegroundWindow.argtypes = [wt.HWND]
u32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
u32.GetForegroundWindow.restype = wt.HWND
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.mouse_event.argtypes = [wt.DWORD, wt.DWORD, wt.DWORD, wt.DWORD, ctypes.c_size_t]
u32.keybd_event.argtypes = [wt.BYTE, wt.BYTE, wt.DWORD, ctypes.c_size_t]

KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_WHEEL = 0x0800


def parse_vk(s):
    return int(s, 0)


def game_hwnd(pid):
    found = []

    def cb(hwnd, lparam):
        t = wt.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(t))
        if t.value == pid and u32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True

    EP = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    u32.EnumWindows(EP(cb), 0)
    return found[0] if found else None


def foreground(hwnd, settle=0.5):
    u32.AttachThreadInput.argtypes = [wt.DWORD, wt.DWORD, wt.BOOL]
    u32.GetWindowThreadProcessId.restype = wt.DWORD
    fg = u32.GetForegroundWindow()
    fg_tid = u32.GetWindowThreadProcessId(fg, None) if fg else 0
    my_tid = k32.GetCurrentThreadId()
    attached = False
    if fg_tid and fg_tid != my_tid:
        attached = bool(u32.AttachThreadInput(my_tid, fg_tid, True))
    try:
        u32.ShowWindow(hwnd, 9)
        u32.SetForegroundWindow(hwnd)
        u32.BringWindowToTop(hwnd)
    finally:
        pass
    time.sleep(settle)
    ok = u32.GetForegroundWindow() == hwnd
    if attached:
        u32.AttachThreadInput(my_tid, fg_tid, False)
    return ok


def tap(vk, hold=0.05):
    u32.keybd_event(vk & 0xFF, 0, 0, 0)
    time.sleep(hold)
    u32.keybd_event(vk & 0xFF, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.04)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["key", "keys", "wheel"])
    ap.add_argument("arg")
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--cx", type=int, default=None)
    ap.add_argument("--cy", type=int, default=None)
    ap.add_argument("--delta", type=int, default=-120)
    ap.add_argument("--pid", type=int, default=None)
    ap.add_argument("--settle", type=float, default=0.4)
    a = ap.parse_args()
    try:
        u32.SetProcessDPIAware()
    except Exception:
        pass
    import w177_core as W
    pid = a.pid or W.pid_of()
    if not pid:
        print("gamemd not running")
        return 2
    hwnd = game_hwnd(pid)
    if not hwnd:
        print("no window")
        return 2
    if not foreground(hwnd, a.settle):
        print("foreground failed")
        return 3
    if a.cmd == "key":
        vk = parse_vk(a.arg)
        for _ in range(a.count):
            tap(vk)
        print("tapped vk=%d count=%d" % (vk, a.count))
    elif a.cmd == "keys":
        for s in a.arg.split(","):
            tap(parse_vk(s.strip()))
        print("tapped sequence %s" % a.arg)
    elif a.cmd == "wheel":
        if a.cx is not None and a.cy is not None:
            u32.SetCursorPos(a.cx, a.cy)
            time.sleep(0.1)
        for _ in range(a.count):
            u32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, a.delta & 0xFFFFFFFF, 0)
            time.sleep(0.08)
        print("wheel delta=%d count=%d at (%s,%s)" % (a.delta, a.count, a.cx, a.cy))
    return 0


if __name__ == "__main__":
    sys.exit(main())
