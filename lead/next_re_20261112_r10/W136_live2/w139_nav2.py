#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W139: navigate to a skirmish and CONFIRM with the frame counter.

What went wrong in W138 (same session): the three NAV_CHAIN clicks were fired 1.8 s
apart, but click 1 starts a *loading* screen ("載入中.."), so clicks 2 and 3 landed on
a loading frame and were lost.

Fix: after every click, wait until the screen is STABLE (two consecutive captures
that are nearly identical) before the next click.  Success is then judged by the
FRAME COUNTER [0xA8ED84], not by a screenshot.

Recipe provenance (all transcribed from qc151_trip.harness8_v4.py):
  NAV_CHAIN  (line 331)  (("mainmenu",700,218),("skirmish",700,304),("start",700,262))
  FRAME_W/H              800 x 600 logical
  _focus_foreground      SW_RESTORE -> BringWindowToTop -> AttachThreadInput+SetForegroundWindow -> ALT
  click_logical          SetCursorPos(left+lx, top+ly) then SendInput DOWN/UP

Usage:
    python -X utf8 w139_nav2.py --launch --go
"""
import argparse
import ctypes
import hashlib
import io
import os
import struct
import subprocess
import sys
import time
import zlib
from ctypes import wintypes as wt

SANDBOX = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W110_crash\out\sandbox_game"
NAV_CHAIN = (("mainmenu", 700, 218), ("skirmish", 700, 304), ("start", 700, 262))
SCREEN_W, SCREEN_H = 1706, 960
FRAME_CTR = 0x00A8ED84

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
for fn, res in (("SetCursorPos", wt.BOOL), ("ShowWindow", wt.BOOL),
                ("BringWindowToTop", wt.BOOL), ("SetForegroundWindow", wt.BOOL),
                ("GetForegroundWindow", wt.HWND)):
    getattr(u32, fn).restype = res
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
u32.BringWindowToTop.argtypes = [wt.HWND]
u32.SetForegroundWindow.argtypes = [wt.HWND]
u32.AttachThreadInput.argtypes = [wt.DWORD, wt.DWORD, wt.BOOL]
u32.AttachThreadInput.restype = wt.BOOL
u32.keybd_event.argtypes = [wt.BYTE, wt.BYTE, wt.DWORD, wt.WPARAM]
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u32.GetWindowThreadProcessId.restype = wt.DWORD
u32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u32.GetClientRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u32.IsWindowVisible.argtypes = [wt.HWND]
k32.GetCurrentThreadId.restype = wt.DWORD
k32.OpenProcess.restype = wt.HANDLE
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", wt.DWORD),
                ("dwFlags", wt.DWORD), ("time", wt.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wt.DWORD), ("mi", MOUSEINPUT)]


u32.SendInput.argtypes = [wt.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
u32.SendInput.restype = wt.UINT


def game_pids():
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-Process gamemd -ErrorAction SilentlyContinue | "
                        "Select-Object -ExpandProperty Id"],
                       capture_output=True, text=True, timeout=60)
    return [int(x) for x in (r.stdout or "").split() if x.strip().isdigit()]


def launch(extra=""):
    ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create "
          "-Arguments @{CommandLine='cmd.exe /c cd /d \"%s\" && start \"\" \"gamemd.exe\" %s'}; "
          "Write-Output ('{0}|{1}' -f $r.ProcessId, $r.ReturnValue)" % (SANDBOX, extra))
    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   capture_output=True, text=True, timeout=120)
    t0 = time.time()
    while time.time() - t0 < 120:
        p = game_pids()
        if p:
            return p[0]
        time.sleep(1.0)
    raise RuntimeError("gamemd did not start")


def find_main_window(pid):
    best = []
    EnumProc = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

    def cb(hwnd, lp):
        t = wt.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(t))
        if t.value != pid or not u32.IsWindowVisible(hwnd):
            return True
        r = wt.RECT()
        u32.GetClientRect(hwnd, ctypes.byref(r))
        if r.right < 200 or r.bottom < 150:
            return True
        best.append((r.right * r.bottom, hwnd))
        return True

    u32.EnumWindows(EnumProc(cb), 0)
    return max(best)[1] if best else None


def rect_of(hwnd):
    r = wt.RECT()
    u32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top


def focus_foreground(hwnd):
    for _ in range(3):
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
        if u32.GetForegroundWindow() == hwnd:
            return True
    return u32.GetForegroundWindow() == hwnd


def click_logical(hwnd, lx, ly):
    left, top = rect_of(hwnd)
    sx, sy = left + lx, top + ly

    def _send(flags):
        inp = INPUT(type=0, mi=MOUSEINPUT(dx=sx, dy=sy, mouseData=0, dwFlags=flags,
                                          time=0, dwExtraInfo=None))
        u32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    u32.SetCursorPos(sx, sy)
    time.sleep(0.05)
    _send(0x0002)
    time.sleep(0.05)
    _send(0x0004)
    return sx, sy


def grab_hash(tag, outdir):
    """capture screen, return (sha1 of raw pixels, png path)"""
    path = os.path.join(outdir, "n2_%s.png" % tag)
    ps = ("Add-Type -AssemblyName System.Drawing;"
          "$b=New-Object System.Drawing.Bitmap(%d,%d);"
          "$g=[System.Drawing.Graphics]::FromImage($b);"
          "$g.CopyFromScreen(0,0,0,0,(New-Object System.Drawing.Size(%d,%d)));"
          "$b.Save('%s',[System.Drawing.Imaging.ImageFormat]::Png);"
          "$g.Dispose();$b.Dispose()" % (SCREEN_W, SCREEN_H, SCREEN_W, SCREEN_H, path))
    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   capture_output=True, timeout=120)
    if not os.path.exists(path):
        return None, None
    return hashlib.sha1(open(path, "rb").read()).hexdigest()[:12], path


class Mem:
    def __init__(self, pid):
        self.h = k32.OpenProcess(0x0010 | 0x1000, False, pid)
        self.fails = 0

    def u32(self, va):
        b = ctypes.create_string_buffer(4)
        got = ctypes.c_size_t(0)
        ok = k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), b, 4, ctypes.byref(got))
        if not ok or got.value != 4:
            self.fails += 1
            return None
        self.fails = 0
        return struct.unpack("<I", b.raw)[0]


def wait_stable(tag, outdir, timeout=45.0, settle=2):
    """wait until two consecutive captures are identical; return (hash, png, waited)"""
    t0 = time.time()
    prev = None
    same = 0
    last_path = None
    while time.time() - t0 < timeout:
        h, p = grab_hash(tag, outdir)
        last_path = p
        if h is not None and h == prev:
            same += 1
            if same >= settle:
                return h, last_path, time.time() - t0
        else:
            same = 0
        prev = h
        time.sleep(0.7)
    return prev, last_path, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--launch", action="store_true")
    ap.add_argument("--pid", type=int)
    ap.add_argument("--go", action="store_true")
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--game-args", default="")
    a = ap.parse_args()

    if a.launch:
        for p in game_pids():
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p)],
                           capture_output=True, timeout=60)
        time.sleep(1)
        pid = launch(a.game_args)
        print("launched pid=%d" % pid)
        time.sleep(9.0)
    elif a.pid:
        pid = a.pid
    else:
        ap.error("need --launch or --pid")

    hwnd = find_main_window(pid)
    if not hwnd:
        print("no main window")
        return 2
    left, top = rect_of(hwnd)
    print("hwnd=0x%X origin=(%d,%d)  focus=%s" % (hwnd, left, top, focus_foreground(hwnd)))

    mem = Mem(pid)
    print("frame counter at start: %s" % mem.u32(FRAME_CTR))

    for i, (name, lx, ly) in enumerate(NAV_CHAIN):
        focus_foreground(hwnd)
        h_before, _, _ = wait_stable("pre%d" % (i + 1), a.outdir, timeout=25)
        sx, sy = click_logical(hwnd, lx, ly)
        print("step %d %-9s click logical=(%d,%d) screen=(%d,%d)  (pre-hash %s)"
              % (i + 1, name, lx, ly, sx, sy, h_before))
        h, p, waited = wait_stable("post%d_%s" % (i + 1, name), a.outdir, timeout=45)
        fc = mem.u32(FRAME_CTR)
        print("        screen stable after %5.1fs  hash=%s  %-28s  frame=%s"
              % (waited, h, os.path.basename(p) if p else "?", fc))
        if h == h_before:
            print("        WARNING: screen unchanged by this click")
        if fc is not None and fc > 0:
            print("        >>> FRAME COUNTER ADVANCING -> we are IN GAME")
            break

    fc = mem.u32(FRAME_CTR)
    print("\nfinal frame counter: %s" % fc)
    print("IN-GAME: %s" % ("YES" if (fc or 0) > 0 else "NO"))
    print("(pid %d left running so the poller can attach)" % pid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
