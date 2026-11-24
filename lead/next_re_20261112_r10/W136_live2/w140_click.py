#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W140: click Network (700,304) from the main menu, capture the next screen.

Rationale from the measurements in this session:
  The main-menu red-band centres measured from my own screenshot are
  220 / 262 / 304 / 345 / 388 / 555  (plus 57 = the "主選單" title bar).
  These match the harness signature `mainmenu: [220,262,304,346,388,556]`.
  Clicking 220 ("單人遊戲") starts a CAMPAIGN load ("載入中..") which then falls
  back to the menu, so campaign is a dead end here.
  YR has no separate "Skirmish" button on the main menu, so Skirmish must sit
  under 網絡 (Network) = band centre 304.

So: launch, focus, click (700,304), wait, capture. One step per run so each
outcome can be inspected instead of guessed.
"""
import ctypes
import os
import subprocess
import sys
import time
from ctypes import wintypes as wt

SANDBOX = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W110_crash\out\sandbox_game"
HERE = os.path.dirname(os.path.abspath(__file__))
SCREEN_W, SCREEN_H = 1706, 960

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


def sh(cmd, t=120):
    return subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                          capture_output=True, text=True, timeout=t)


def pids():
    r = sh("(Get-Process gamemd -ErrorAction SilentlyContinue).Id")
    return [int(x) for x in (r.stdout or "").split() if x.strip().isdigit()]


def launch():
    # build the command line carefully: no nested escaping beyond the sandbox path
    inner = 'cmd.exe /c cd /d "{0}" ^&^& start "" "gamemd.exe"'.format(SANDBOX)
    ps = ('$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create '
          '-Arguments @{CommandLine=\'%s\'}; Write-Output $r.ReturnValue' % inner)
    out = sh(ps)
    print("  launch rc/out: %r %r" % (out.returncode, (out.stdout or "").strip()[:80]))
    t0 = time.time()
    while time.time() - t0 < 90:
        p = pids()
        if p:
            return p[0]
        time.sleep(1)
    return None


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
    time.sleep(0.2)
    u32.BringWindowToTop(hwnd)
    if u32.GetForegroundWindow() == hwnd:
        return True
    cur = k32.GetCurrentThreadId()
    tgt = u32.GetWindowThreadProcessId(hwnd, None)
    u32.AttachThreadInput(cur, tgt, True)
    u32.SetForegroundWindow(hwnd)
    u32.AttachThreadInput(cur, tgt, False)
    time.sleep(0.3)
    if u32.GetForegroundWindow() == hwnd:
        return True
    u32.keybd_event(0x12, 0, 0, 0)
    u32.keybd_event(0x12, 0, 2, 0)
    u32.SetForegroundWindow(hwnd)
    time.sleep(0.3)
    return u32.GetForegroundWindow() == hwnd


def click(x, y):
    u32.SetCursorPos(x, y)
    time.sleep(0.08)
    for f in (0x0002, 0x0004):
        i = INP(type=0, mi=MI(dx=x, dy=y, mouseData=0, dwFlags=f, time=0,
                              dwExtraInfo=None))
        u32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INP))
        time.sleep(0.08)


def shot(name):
    p = os.path.join(HERE, name + ".png")
    ps = ("Add-Type -AssemblyName System.Drawing;"
          "$b=New-Object System.Drawing.Bitmap(%d,%d);"
          "$g=[System.Drawing.Graphics]::FromImage($b);"
          "$g.CopyFromScreen(0,0,0,0,(New-Object System.Drawing.Size(%d,%d)));"
          "$b.Save('%s',[System.Drawing.Imaging.ImageFormat]::Png);"
          "$g.Dispose();$b.Dispose()" % (SCREEN_W, SCREEN_H, SCREEN_W, SCREEN_H, p))
    sh(ps)
    return p if os.path.exists(p) else None


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "304"
    xy = {"304": (700, 304), "262": (700, 262), "220": (700, 220)}
    x, y = xy.get(which, (700, 304))

    for p in pids():
        sh("taskkill /F /T /PID %d" % p)
    time.sleep(1)

    pid = launch()
    if not pid:
        print("FAILED to launch gamemd")
        return 2
    print("pid=%d, waiting 10s" % pid)
    time.sleep(10)

    hwnd = find_win(pid)
    if not hwnd:
        print("no window")
        return 2
    print("hwnd=0x%X focus=%s" % (hwnd, focus(hwnd)))
    shot("w140_before")
    click(x, y)
    print("clicked (%d,%d)" % (x, y))
    time.sleep(5)
    print("after: %s" % shot("w140_after"))
    print("pid still running: %r" % pids())
    return 0


if __name__ == "__main__":
    sys.exit(main())
