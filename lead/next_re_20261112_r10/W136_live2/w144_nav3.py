#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W144: navigate to a skirmish -- NOW THAT CLICKS WORK.

Root cause of every earlier failure (ledger §887):
  With cnc-ddraw `windowed=true`, the game window is NOT at (0,0) and NOT the
  configured size.  Measured: client 533x400 at window origin (587,280).
  All earlier attempts clicked at screen (700,304) etc., i.e. OUTSIDE the window.
  Fix: map logical (800x600) -> client -> screen with ClientToScreen, every time.

Click efficacy is judged by GAME STATE, never by screenshots (the menu background
animates -- ledger §886):
  - the process exiting after clicking EXIT proved the pipeline works;
  - for navigation we watch the logical frame counter [0xA8ED84], which is 0 in
    the menus and starts advancing once a scenario is running.

Usage:
    python -X utf8 w144_nav3.py --go
"""
import argparse
import ctypes
import io
import os
import struct
import subprocess
import sys
import time
from ctypes import wintypes as wt

SB = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W110_crash\out\sandbox_game"
FRAME_CTR = 0x00A8ED84
MODE = 0x00A8B238

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
u32.GetForegroundWindow.restype = wt.HWND
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
u32.BringWindowToTop.argtypes = [wt.HWND]
u32.SetForegroundWindow.argtypes = [wt.HWND]
u32.AttachThreadInput.argtypes = [wt.DWORD, wt.DWORD, wt.BOOL]
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u32.GetWindowThreadProcessId.restype = wt.DWORD
u32.GetClientRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u32.ClientToScreen.argtypes = [wt.HWND, ctypes.POINTER(wt.POINT)]
u32.IsWindowVisible.argtypes = [wt.HWND]
u32.IsWindowVisible.restype = wt.BOOL
k32.GetCurrentThreadId.restype = wt.DWORD
k32.OpenProcess.restype = wt.HANDLE
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]


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


def pids():
    return [int(x) for x in sh("(Get-Process gamemd -ErrorAction SilentlyContinue).Id").split()
            if x.strip().isdigit()]


def find_win(pid):
    best = []
    EP = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

    def cb(h, l):
        t = wt.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(t))
        if t.value == pid and u32.IsWindowVisible(h):
            r = wt.RECT()
            u32.GetClientRect(h, ctypes.byref(r))
            if r.right > 100 and r.bottom > 100:
                best.append((r.right * r.bottom, h, r.right, r.bottom))
        return True

    u32.EnumWindows(EP(cb), 0)
    best.sort(reverse=True)
    return best[0] if best else None


def geom(hwnd):
    r = wt.RECT()
    u32.GetClientRect(hwnd, ctypes.byref(r))
    cw, ch = r.right, r.bottom
    p = wt.POINT()
    p.x = 0
    p.y = 0
    u32.ClientToScreen(hwnd, ctypes.byref(p))
    return cw, ch, p.x, p.y


def focus(hwnd):
    u32.ShowWindow(hwnd, 9)
    time.sleep(0.25)
    u32.BringWindowToTop(hwnd)
    if u32.GetForegroundWindow() == hwnd:
        return True
    cur = k32.GetCurrentThreadId()
    tgt = u32.GetWindowThreadProcessId(hwnd, None)
    u32.AttachThreadInput(cur, tgt, True)
    u32.SetForegroundWindow(hwnd)
    u32.AttachThreadInput(cur, tgt, False)
    time.sleep(0.35)
    return u32.GetForegroundWindow() == hwnd


def to_screen(hwnd, lx, ly):
    cw, ch, ox, oy = geom(hwnd)
    return ox + int(round(lx * cw / 800.0)), oy + int(round(ly * ch / 600.0))


def click_logical(hwnd, lx, ly):
    sx, sy = to_screen(hwnd, lx, ly)
    u32.SetCursorPos(sx, sy)
    time.sleep(0.2)
    for f in (0x0002, 0x0004):
        i = INP(type=0, mi=MI(dx=sx, dy=sy, mouseData=0, dwFlags=f, time=0,
                              dwExtraInfo=None))
        u32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INP))
        time.sleep(0.12)
    return sx, sy


class Mem:
    def __init__(self, pid):
        self.h = k32.OpenProcess(0x0010 | 0x1000, False, pid)

    def u32(self, va):
        b = ctypes.create_string_buffer(4)
        got = ctypes.c_size_t(0)
        ok = k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), b, 4, ctypes.byref(got))
        return struct.unpack("<I", b.raw)[0] if (ok and got.value == 4) else None


def launch():
    ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create "
          "-Arguments @{CommandLine='cmd.exe /c cd /d \"%s\" && start \"\" \"gamemd.exe\"'}; "
          "Write-Output $r.ReturnValue" % SB)
    sh(ps)
    t0 = time.time()
    while time.time() - t0 < 90:
        p = pids()
        if p:
            return p[0]
        time.sleep(1)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--go", action="store_true")
    ap.add_argument("--click", nargs=2, type=int, metavar=("LX", "LY"))
    ap.add_argument("--wait", type=float, default=12.0)
    a = ap.parse_args()

    for p in pids():
        sh("taskkill /F /T /PID %d" % p)
    time.sleep(2)

    pid = launch()
    if not pid:
        print("launch failed")
        return 2
    print("pid=%d, waiting 10s" % pid)
    time.sleep(10)

    w = find_win(pid)
    if not w:
        print("no window")
        return 2
    _, hwnd, cw, ch = w
    cw2, ch2, ox, oy = geom(hwnd)
    print("client=%dx%d origin=(%d,%d) focus=%s" % (cw2, ch2, ox, oy, focus(hwnd)))

    mem = Mem(pid)
    print("frame=%s mode=%s" % (mem.u32(FRAME_CTR), mem.u32(MODE)))

    if a.click:
        lx, ly = a.click
        sx, sy = click_logical(hwnd, lx, ly)
        print("clicked logical (%d,%d) -> screen (%d,%d)" % (lx, ly, sx, sy))
        time.sleep(a.wait)
        print("after: frame=%s mode=%s alive=%r"
              % (mem.u32(FRAME_CTR), mem.u32(MODE), bool(pids())))
        return 0

    if not a.go:
        return 0

    # main menu: 單人遊戲 220 / 網際網路遊戲 262 / 網絡 304 / 動畫 346 / 選項 388 / 退出 556
    plan = [("網絡(Network)", 700, 304)]
    for name, lx, ly in plan:
        focus(hwnd)
        before = mem.u32(MODE)
        sx, sy = click_logical(hwnd, lx, ly)
        print("step %-16s logical=(%d,%d) screen=(%d,%d) mode %s ->"
              % (name, lx, ly, sx, sy, before), end=" ")
        time.sleep(4)
        print("%s frame=%s" % (mem.u32(MODE), mem.u32(FRAME_CTR)))

    print("\nleaving pid=%d running" % pid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
