#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W141: decisive click experiment — gradual move then click, against the EXIT button.

Why EXIT: its band x-range is known precisely (635..769, centre 702) because the
radar graphic does not reach that height, so the measurement is unambiguous.

Hypothesis under test: RA2's buttons only accept a click once the UI has processed
a WM_MOUSEMOVE that puts the button in its "hot" state.  A single SetCursorPos
immediately followed by LEFTDOWN may be too abrupt, so the click is swallowed.
Fix attempted: approach the target pixel in 25 small steps, then pause, then click.

Outcome is binary and self-evident: if the game exits, the pipeline works.
"""
import ctypes
import subprocess
import sys
import time
from ctypes import wintypes as wt

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
u32.GetForegroundWindow.restype = wt.HWND
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.GetCursorPos.argtypes = [ctypes.POINTER(wt.POINT)]
u32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
u32.BringWindowToTop.argtypes = [wt.HWND]
u32.SetForegroundWindow.argtypes = [wt.HWND]
u32.AttachThreadInput.argtypes = [wt.DWORD, wt.DWORD, wt.BOOL]
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u32.GetWindowThreadProcessId.restype = wt.DWORD
u32.GetClientRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u32.IsWindowVisible.argtypes = [wt.HWND]
k32.GetCurrentThreadId.restype = wt.DWORD


class MI(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", wt.DWORD),
                ("dwFlags", wt.DWORD), ("time", wt.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class INP(ctypes.Structure):
    _fields_ = [("type", wt.DWORD), ("mi", MI)]


u32.SendInput.argtypes = [wt.UINT, ctypes.POINTER(INP), ctypes.c_int]
u32.SendInput.restype = wt.UINT


def sh(cmd, t=60):
    return subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                          capture_output=True, text=True, timeout=t).stdout.strip()


def pids():
    out = sh("(Get-Process gamemd -ErrorAction SilentlyContinue).Id")
    return [int(x) for x in out.split() if x.strip().isdigit()]


def find_win(pid):
    best = []
    EP = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

    def cb(h, l):
        t = wt.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(t))
        if t.value == pid and u32.IsWindowVisible(h):
            r = wt.RECT()
            u32.GetClientRect(h, ctypes.byref(r))
            if r.right > 200 and r.bottom > 150:
                best.append((r.right * r.bottom, h))
        return True

    u32.EnumWindows(EP(cb), 0)
    best.sort(reverse=True)
    return best[0][1] if best else None


def focus(hwnd):
    u32.ShowWindow(hwnd, 9)
    time.sleep(0.3)
    u32.BringWindowToTop(hwnd)
    if u32.GetForegroundWindow() == hwnd:
        return True
    cur = k32.GetCurrentThreadId()
    tgt = u32.GetWindowThreadProcessId(hwnd, None)
    u32.AttachThreadInput(cur, tgt, True)
    u32.SetForegroundWindow(hwnd)
    u32.AttachThreadInput(cur, tgt, False)
    time.sleep(0.4)
    return u32.GetForegroundWindow() == hwnd


def cursor():
    pt = wt.POINT()
    u32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def move_gradual(x, y, steps=25):
    sx, sy = cursor()
    for k in range(1, steps + 1):
        nx = int(sx + (x - sx) * k / float(steps))
        ny = int(sy + (y - sy) * k / float(steps))
        u32.SetCursorPos(nx, ny)
        time.sleep(0.012)
    u32.SetCursorPos(x, y)
    time.sleep(0.30)


def send_click(x, y):
    for f in (0x0002, 0x0004):
        i = INP(type=0, mi=MI(dx=x, dy=y, mouseData=0, dwFlags=f, time=0,
                              dwExtraInfo=None))
        u32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INP))
        time.sleep(0.12)


def main():
    p = pids()
    if not p:
        print("no gamemd running")
        return 2
    pid = p[0]
    hwnd = find_win(pid)
    print("pid=%d hwnd=0x%X focus=%s cursor=%r" % (pid, hwnd, focus(hwnd), cursor()))

    x, y = 702, 556        # 退出遊戲 : band x 635..769 -> centre 702, y centre 556
    print("--- EXIT click with gradual move ---")
    move_gradual(x, y)
    print("   cursor now %r (target %r)" % (cursor(), (x, y)))
    send_click(x, y)
    print("   clicked")

    for k in range(10):
        time.sleep(1)
        if not pids():
            print("   >>> t=%ds GAME EXITED -- click pipeline WORKS" % (k + 1))
            return 0
    print("   >>> still running after 10s -- click still swallowed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
