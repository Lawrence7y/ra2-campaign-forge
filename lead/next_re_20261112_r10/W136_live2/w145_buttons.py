#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W145: enumerate the game's real Win32 menu buttons and click them by exact position.

Breakthrough (ledger §887): YR builds its menus out of REAL Win32 child controls
(class `Button` inside a `#32770`), so the button rectangles are available from
Windows itself -- no screenshot measuring, no guessing.

Evidence that this works: clicking the centre of the control whose rect is
(429,189,104x28) changed the game's mode selector [0xA8B238] from 0 to 3, and
WindowFromPoint at that pixel returned exactly that button's hwnd.

This tool:
  --list            enumerate buttons of the current screen (hwnd, ctrl id, rect, centre)
  --click ID|INDEX  click that control by its exact screen centre
  --state           print mode + frame counter
It never guesses coordinates: it always asks Windows where the control is.
"""
import argparse
import ctypes
import struct
import subprocess
import sys
import time
from ctypes import wintypes as wt

FRAME = 0x00A8ED84
MODE = 0x00A8B238

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
u32.BringWindowToTop.argtypes = [wt.HWND]
u32.SetForegroundWindow.argtypes = [wt.HWND]
u32.AttachThreadInput.argtypes = [wt.DWORD, wt.DWORD, wt.BOOL]
u32.GetForegroundWindow.restype = wt.HWND
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u32.GetWindowThreadProcessId.restype = wt.DWORD
u32.GetParent.argtypes = [wt.HWND]
u32.GetParent.restype = wt.HWND
u32.GetWindow.argtypes = [wt.HWND, wt.UINT]
u32.GetWindow.restype = wt.HWND
u32.GetClassNameA.argtypes = [wt.HWND, ctypes.c_char_p, ctypes.c_int]
u32.GetWindowTextA.argtypes = [wt.HWND, ctypes.c_char_p, ctypes.c_int]
u32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u32.GetWindowLongA.argtypes = [wt.HWND, ctypes.c_int]
u32.GetWindowLongA.restype = ctypes.c_long
u32.IsWindowVisible.argtypes = [wt.HWND]
u32.IsWindowVisible.restype = wt.BOOL
u32.WindowFromPoint.argtypes = [wt.POINT]
u32.WindowFromPoint.restype = wt.HWND
u32.SendMessageA.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
u32.SendMessageA.restype = ctypes.c_long
k32.GetCurrentThreadId.restype = wt.DWORD
k32.OpenProcess.restype = wt.HANDLE
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

GW_CHILD = 5
GW_HWNDNEXT = 2
GWL_ID = -12
WM_GETTEXT = 0x000D
WM_GETTEXTLENGTH = 0x000E


class MI(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", wt.DWORD),
                ("dwFlags", wt.DWORD), ("time", wt.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class INP(ctypes.Structure):
    _fields_ = [("type", wt.DWORD), ("mi", MI)]


u32.SendInput.argtypes = [wt.UINT, ctypes.POINTER(INP), ctypes.c_int]
u32.SendInput.restype = wt.UINT


def sh(c, t=60):
    return subprocess.run(["powershell", "-NoProfile", "-Command", c],
                          capture_output=True, text=True, timeout=t).stdout.strip()


def pid():
    o = sh("(Get-Process gamemd -ErrorAction SilentlyContinue).Id")
    return int(o.split()[0]) if o else None


def proc(pid_):
    return k32.OpenProcess(0x0010 | 0x1000, False, pid_)


def rd(h, va):
    b = ctypes.create_string_buffer(4)
    g = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(h, ctypes.c_void_p(va), b, 4, ctypes.byref(g))
    return struct.unpack("<I", b.raw)[0] if ok and g.value == 4 else None


def text_of(h):
    n = u32.SendMessageA(h, WM_GETTEXTLENGTH, 0, 0)
    if not n:
        return ""
    buf = ctypes.create_string_buffer(n + 2)
    u32.SendMessageA(h, WM_GETTEXT, n + 1, ctypes.addressof(buf))
    return buf.value.decode("latin-1", "replace")


def root_windows(pid_):
    out = []
    EP = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

    def cb(h, l):
        t = wt.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(t))
        if t.value == pid_ and u32.IsWindowVisible(h):
            r = wt.RECT()
            u32.GetWindowRect(h, ctypes.byref(r))
            if r.right - r.left > 100 and r.bottom - r.top > 100:
                out.append(h)
        return True

    u32.EnumWindows(EP(cb), 0)
    return out


def collect_buttons(pid_):
    """walk every child of every top window; return visible Buttons with screen rects"""
    rows = []

    def walk(h, depth=0):
        c = u32.GetWindow(h, GW_CHILD)
        while c:
            cls = ctypes.create_string_buffer(64)
            u32.GetClassNameA(c, cls, 64)
            cn = cls.value.decode("latin-1", "replace")
            r = wt.RECT()
            u32.GetWindowRect(c, ctypes.byref(r))
            w, hh = r.right - r.left, r.bottom - r.top
            if cn == "Button" and w > 8 and hh > 8 and u32.IsWindowVisible(c):
                rows.append({
                    "hwnd": int(c), "ctrl_id": u32.GetWindowLongA(c, GWL_ID),
                    "text": text_of(c), "x": r.left, "y": r.top, "w": w, "h": hh,
                    "cx": r.left + w // 2, "cy": r.top + h // 2, "depth": depth})
            walk(c, depth + 1)
            c = u32.GetWindow(c, GW_HWNDNEXT)

    for top in root_windows(pid_):
        walk(top)
    rows.sort(key=lambda d: (d["y"], d["x"]))
    return rows


def focus_game(pid_):
    tops = root_windows(pid_)
    if not tops:
        return None
    g = tops[0]
    u32.ShowWindow(g, 9)
    time.sleep(0.2)
    u32.BringWindowToTop(g)
    if u32.GetForegroundWindow() != g:
        cur = k32.GetCurrentThreadId()
        tgt = u32.GetWindowThreadProcessId(g, None)
        u32.AttachThreadInput(cur, tgt, True)
        u32.SetForegroundWindow(g)
        u32.AttachThreadInput(cur, tgt, False)
        time.sleep(0.3)
    return g


def click_at(x, y):
    u32.SetCursorPos(x, y)
    time.sleep(0.2)
    for f in (0x0002, 0x0004):
        i = INP(type=0, mi=MI(dx=x, dy=y, mouseData=0, dwFlags=f, time=0,
                              dwExtraInfo=None))
        u32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INP))
        time.sleep(0.12)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--state", action="store_true")
    ap.add_argument("--click-id", type=int)
    ap.add_argument("--click-index", type=int)
    ap.add_argument("--settle", type=float, default=3.0)
    a = ap.parse_args()

    p = pid()
    if not p:
        print("gamemd not running")
        return 2
    h = proc(p)

    if a.state:
        print("mode=%s frame=%s" % (rd(h, MODE), rd(h, FRAME)))
        return 0

    rows = collect_buttons(p)
    if a.list or (a.click_id is None and a.click_index is None):
        print("pid=%d  mode=%s frame=%s  buttons=%d"
              % (p, rd(h, MODE), rd(h, FRAME), len(rows)))
        print("%-4s %-12s %-8s %-22s %-22s %s"
              % ("idx", "hwnd", "ctrl_id", "rect", "text", "centre"))
        for i, d in enumerate(rows):
            print("%-4d %-12s %-8d (%4d,%4d,%3dx%-3d)      %-22r (%d,%d)"
                  % (i, hex(d["hwnd"]), d["ctrl_id"], d["x"], d["y"], d["w"], d["h"],
                     d["text"][:22], d["cx"], d["cy"]))
        return 0

    target = None
    if a.click_id is not None:
        target = next((d for d in rows if d["ctrl_id"] == a.click_id), None)
    elif a.click_index is not None:
        target = rows[a.click_index] if 0 <= a.click_index < len(rows) else None
    if not target:
        print("target not found")
        return 2

    focus_game(p)
    hit = u32.WindowFromPoint(wt.POINT(target["cx"], target["cy"]))
    print("target hwnd=0x%X ctrl_id=%d text=%r centre=(%d,%d)"
          % (target["hwnd"], target["ctrl_id"], target["text"],
             target["cx"], target["cy"]))
    print("WindowFromPoint(centre)=0x%X  match=%s"
          % (hit, hit == target["hwnd"]))
    before = (rd(h, MODE), rd(h, FRAME))
    click_at(target["cx"], target["cy"])
    time.sleep(a.settle)
    after = (rd(h, MODE), rd(h, FRAME))
    print("mode/frame: %s -> %s   CHANGED=%s" % (before, after, before != after))
    return 0


if __name__ == "__main__":
    sys.exit(main())
