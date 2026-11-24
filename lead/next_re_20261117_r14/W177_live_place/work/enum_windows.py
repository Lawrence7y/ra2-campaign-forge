#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""纯枚举：列出 gamemd 的所有顶层窗口（含不可见），判断是否弹出了对话框。"""
import ctypes
import subprocess
import sys
from ctypes import wintypes as wt

u32 = ctypes.windll.user32
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u32.GetWindowTextA.argtypes = [wt.HWND, ctypes.c_char_p, ctypes.c_int]
u32.GetClassNameA.argtypes = [wt.HWND, ctypes.c_char_p, ctypes.c_int]
u32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u32.GetForegroundWindow.restype = wt.HWND


def pid_of(name="gamemd"):
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-Process %s -ErrorAction SilentlyContinue).Id" % name],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


def main():
    pid = pid_of()
    if not pid:
        print("no gamemd")
        return 2
    found = []

    def cb(hwnd, lparam):
        t = wt.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(t))
        if t.value == pid:
            buf = ctypes.create_string_buffer(256)
            cls = ctypes.create_string_buffer(256)
            u32.GetWindowTextA(hwnd, buf, 256)
            u32.GetClassNameA(hwnd, cls, 256)
            r = wt.RECT()
            u32.GetWindowRect(hwnd, ctypes.byref(r))
            found.append((hwnd, buf.value.decode("latin-1", "replace"),
                          cls.value.decode("latin-1", "replace"), u32.IsWindowVisible(hwnd),
                          (r.left, r.top, r.right, r.bottom)))
        return True

    EP = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    u32.EnumWindows(EP(cb), 0)
    print("foreground=0x%X" % u32.GetForegroundWindow())
    print("gamemd pid=%d windows=%d" % (pid, len(found)))
    for hwnd, title, cls, vis, rect in found:
        print("  0x%X vis=%d cls=%r title=%r rect=%s" % (hwnd, vis, cls, title, rect))
    return 0


if __name__ == "__main__":
    sys.exit(main())
