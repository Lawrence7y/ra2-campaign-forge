#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W142: enumerate every window of gamemd (top-level + children) with rects.

Hypothesis being tested: the game renders only 798x598 of a 1706x960 window, which
suggests the *input* surface may be a different (child) window than the one I have
been clicking.  If a child window exists at ~798x598, that is the real click target.
"""
import ctypes
import subprocess
import sys
from ctypes import wintypes as wt

u32 = ctypes.windll.user32
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u32.GetWindowThreadProcessId.restype = wt.DWORD
u32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u32.GetWindowRect.restype = wt.BOOL
u32.GetClientRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u32.GetClientRect.restype = wt.BOOL
u32.GetClassNameA.argtypes = [wt.HWND, ctypes.c_char_p, ctypes.c_int]
u32.GetClassNameA.restype = ctypes.c_int
u32.GetWindowTextA.argtypes = [wt.HWND, ctypes.c_char_p, ctypes.c_int]
u32.GetWindowTextA.restype = ctypes.c_int
u32.GetParent.argtypes = [wt.HWND]
u32.GetParent.restype = wt.HWND
u32.IsWindowVisible.argtypes = [wt.HWND]
u32.IsWindowVisible.restype = wt.BOOL
u32.EnumWindows.argtypes = [ctypes.c_void_p, wt.LPARAM]
u32.EnumWindows.restype = wt.BOOL
u32.EnumChildWindows.argtypes = [wt.HWND, ctypes.c_void_p, wt.LPARAM]
u32.EnumChildWindows.restype = wt.BOOL


def pids():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-Process gamemd -ErrorAction SilentlyContinue).Id"],
                         capture_output=True, text=True, timeout=30).stdout.strip()
    return [int(x) for x in out.split() if x.strip().isdigit()]


def main():
    p = pids()
    if not p:
        print("no gamemd")
        return 2
    pid = p[0]
    rows = []
    EP = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

    def cb(h, l):
        t = wt.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(t))
        if t.value != pid:
            return True
        cls = ctypes.create_string_buffer(256)
        u32.GetClassNameA(h, cls, 256)
        txt = ctypes.create_string_buffer(256)
        u32.GetWindowTextA(h, txt, 256)
        r = wt.RECT()
        u32.GetWindowRect(h, ctypes.byref(r))
        c = wt.RECT()
        u32.GetClientRect(h, ctypes.byref(c))
        par = u32.GetParent(h)
        rows.append((int(h), cls.value.decode("latin-1", "replace"),
                     txt.value.decode("latin-1", "replace"),
                     r.left, r.top, r.right - r.left, r.bottom - r.top,
                     c.right, c.bottom, bool(u32.IsWindowVisible(h)), bool(par)))
        return True

    u32.EnumWindows(EP(cb), 0)
    u32.EnumChildWindows(0, EP(cb), 0)

    seen = set()
    print("pid=%d\n" % pid)
    print("%-12s %-24s %-18s %-22s %-12s %-5s %-6s"
          % ("hwnd", "class", "title", "rect(L,T,WxH)", "client", "vis", "child"))
    for h, cls, txt, l, t, w, hh, cw, ch, vis, isch in rows:
        if h in seen:
            continue
        seen.add(h)
        print("%-12s %-24s %-18s (%4d,%4d,%4dx%-4d) %4dx%-4d    %-5s %s"
              % (hex(h), cls[:24], txt[:18], l, t, w, hh, cw, ch, vis, isch))
    return 0


if __name__ == "__main__":
    sys.exit(main())
