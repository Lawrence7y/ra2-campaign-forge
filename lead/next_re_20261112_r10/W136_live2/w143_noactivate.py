#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W143: does cnc-ddraw's `noactivateapp=true` swallow my synthetic clicks?

Hypothesis: cnc-ddraw's `noactivateapp` option stops the game window from becoming
ACTIVE.  GetForegroundWindow() still reports the window (so my earlier checks passed),
but the game may never treat itself as focused and therefore ignores mouse input.
That would explain every failed click in this session.

Test design (binary, no screenshots):
  - patch `[gamemd] noactivateapp` to the requested value,
  - launch,
  - click the EXIT button (band x 635..769 -> x=702, y=556),
  - if gamemd exits -> the click reached the UI; if it survives -> still swallowed.
Screenshots are deliberately NOT the criterion (the menu background animates).

ddraw.ini is backed up before the first patch and restored by --restore.

Usage:
    python -X utf8 w143_noactivate.py --value false
    python -X utf8 w143_noactivate.py --value true
    python -X utf8 w143_noactivate.py --restore
"""
import argparse
import ctypes
import io
import os
import re
import shutil
import subprocess
import sys
import time
from ctypes import wintypes as wt

SB = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W110_crash\out\sandbox_game"
INI = os.path.join(SB, "ddraw.ini")
EXIT_XY = (702, 556)

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
u32.IsWindowVisible.restype = wt.BOOL
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
                          capture_output=True, text=True, timeout=t).stdout.strip()


def pids():
    return [int(x) for x in sh("(Get-Process gamemd -ErrorAction SilentlyContinue).Id").split()
            if x.strip().isdigit()]


def killall():
    for p in pids():
        sh("taskkill /F /T /PID %d" % p)
    time.sleep(2)


def patch_section(name, key, value):
    """set `key=value` inside [name]; create if absent."""
    t = io.open(INI, encoding="latin-1").read()
    m = re.search(r"(?m)^\[" + re.escape(name) + r"\]\s*$", t)
    if not m:
        raise SystemExit("section [%s] not found" % name)
    start = m.end()
    nxt = re.search(r"(?m)^\[", t[start:])
    end = start + (nxt.start() if nxt else len(t) - start)
    body = t[start:end]
    if re.search(r"(?m)^\s*" + re.escape(key) + r"\s*=", body):
        body2 = re.sub(r"(?m)^(\s*" + re.escape(key) + r"\s*=).*$",
                       r"\g<1>" + value, body, count=1)
    else:
        body2 = body.rstrip("\r\n") + "\n" + key + "=" + value + "\n"
    return t[:start] + body2 + t[end:]


def read_section(name):
    t = io.open(INI, encoding="latin-1").read()
    m = re.search(r"(?m)^\[" + re.escape(name) + r"\]\s*$", t)
    if not m:
        return ""
    start = m.end()
    nxt = re.search(r"(?m)^\[", t[start:])
    end = start + (nxt.start() if nxt else len(t) - start)
    return t[start:end]


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
                best.append((r.right * r.bottom, h, r.right, r.bottom))
        return True

    u32.EnumWindows(EP(cb), 0)
    best.sort(reverse=True)
    return best[0] if best else None


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


def click(x, y):
    u32.SetCursorPos(x, y)
    time.sleep(0.2)
    for f in (0x0002, 0x0004):
        i = INP(type=0, mi=MI(dx=x, dy=y, mouseData=0, dwFlags=f, time=0,
                              dwExtraInfo=None))
        u32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INP))
        time.sleep(0.12)


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
    ap.add_argument("--value", choices=["true", "false"])
    ap.add_argument("--restore", action="store_true")
    a = ap.parse_args()

    if a.restore:
        b = os.path.join(SB, "ddraw.ini.bak_live_20261115_192919")
        if not os.path.exists(b):
            print("backup missing")
            return 2
        shutil.copy2(b, INI)
        print("restored ddraw.ini from backup; [gamemd] now:")
        print(read_section("gamemd"))
        return 0

    if not a.value:
        ap.error("--value or --restore")

    killall()
    t = patch_section("gamemd", "noactivateapp", a.value)
    io.open(INI, "w", encoding="latin-1", newline="").write(t)
    print("[gamemd] after patch:")
    print(read_section("gamemd").strip())
    print()

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
    print("window client = %dx%d" % (cw, ch))
    print("focus = %s" % focus(hwnd))

    print("clicking EXIT at %r ..." % (EXIT_XY,))
    click(*EXIT_XY)

    exited = False
    for k in range(12):
        time.sleep(1)
        if not pids():
            exited = True
            print("  >>> t=%ds GAME EXITED  ==> click REACHED the UI" % (k + 1))
            break
    if not exited:
        print("  >>> still running after 12s ==> click still swallowed")
    return 0 if exited else 1


if __name__ == "__main__":
    sys.exit(main())
