#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W138: enter a skirmish using the harness's PROVEN navigation recipe.

Everything here is transcribed from
`lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py`:

  NAV_CHAIN   (line 331): (("mainmenu",700,218),("skirmish",700,304),("start",700,262))
  FRAME_W/H   (line ~337): 800 x 600   -- game logical resolution
  _focus_foreground (line 2376): SW_RESTORE -> BringWindowToTop ->
                                 AttachThreadInput + SetForegroundWindow -> ALT bypass
  click_logical (line 2291): SetCursorPos(left+lx, top+ly) then SendInput DOWN/UP

My earlier failures (ledger §884-7) used (730,237) -- a coordinate I estimated from
a screenshot -- and never called AttachThreadInput.  Both are fixed here.

This script does NOT copy the harness: it re-implements only these four pieces, so
the trip script's QC gates and file handling stay untouched.

Usage:
    python -X utf8 w138_nav.py --launch --probe      # launch, report, no clicks
    python -X utf8 w138_nav.py --launch --go         # launch and navigate
"""
import argparse
import ctypes
import io
import os
import subprocess
import sys
import time
from ctypes import wintypes as wt

SANDBOX = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W110_crash\out\sandbox_game"

NAV_CHAIN = (("mainmenu", 700, 218), ("skirmish", 700, 304), ("start", 700, 262))
FRAME_W, FRAME_H = 800, 600
MAIN_WINDOW_TITLE = "Yuri's Revenge"

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.SetCursorPos.restype = wt.BOOL
u32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
u32.ShowWindow.restype = wt.BOOL
u32.BringWindowToTop.argtypes = [wt.HWND]
u32.BringWindowToTop.restype = wt.BOOL
u32.SetForegroundWindow.argtypes = [wt.HWND]
u32.SetForegroundWindow.restype = wt.BOOL
u32.GetForegroundWindow.restype = wt.HWND
u32.AttachThreadInput.argtypes = [wt.DWORD, wt.DWORD, wt.BOOL]
u32.AttachThreadInput.restype = wt.BOOL
u32.keybd_event.argtypes = [wt.BYTE, wt.BYTE, wt.DWORD, wt.WPARAM]
u32.keybd_event.restype = None
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u32.GetWindowThreadProcessId.restype = wt.DWORD
u32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u32.GetClientRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u32.IsWindowVisible.argtypes = [wt.HWND]
u32.GetWindowTextA.argtypes = [wt.HWND, ctypes.c_char_p, ctypes.c_int]
k32.GetCurrentThreadId.restype = wt.DWORD


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", wt.DWORD), ("dwFlags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wt.DWORD), ("mi", MOUSEINPUT)]


u32.SendInput.argtypes = [wt.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
u32.SendInput.restype = wt.UINT


def rect_of(hwnd):
    r = wt.RECT()
    u32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right - r.left, r.bottom - r.top


def find_main_window(pid):
    best = []
    EnumProc = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

    def cb(hwnd, lp):
        t = wt.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(t))
        if t.value != pid or not u32.IsWindowVisible(hwnd):
            return True
        buf = ctypes.create_string_buffer(256)
        u32.GetWindowTextA(hwnd, buf, 256)
        title = buf.value.decode("latin-1", "replace")
        r = wt.RECT()
        u32.GetClientRect(hwnd, ctypes.byref(r))
        w, h = r.right, r.bottom
        if w < 200 or h < 150:
            return True
        best.append((w * h, hwnd, title, w, h))
        return True

    u32.EnumWindows(EnumProc(cb), 0)
    if not best:
        return None
    best.sort(reverse=True)
    return best[0]


def focus_foreground(hwnd, trail):
    """harness _focus_foreground, transcribed"""
    for i in range(3):
        u32.ShowWindow(hwnd, 9)               # SW_RESTORE
        time.sleep(0.2)
        u32.BringWindowToTop(hwnd)
        fg = u32.GetForegroundWindow()
        trail.append(("bring_to_top", i + 1, fg == hwnd))
        if fg == hwnd:
            return True
        cur = k32.GetCurrentThreadId()
        tgt = u32.GetWindowThreadProcessId(hwnd, None)
        u32.AttachThreadInput(cur, tgt, True)
        u32.SetForegroundWindow(hwnd)
        u32.AttachThreadInput(cur, tgt, False)
        time.sleep(0.3)
        if u32.GetForegroundWindow() == hwnd:
            return True
        # ALT bypass of the foreground lock
        u32.keybd_event(0x12, 0, 0, 0)
        u32.keybd_event(0x12, 0, 2, 0)
        u32.SetForegroundWindow(hwnd)
        time.sleep(0.3)
        trail.append(("alt_bypass", i + 1, u32.GetForegroundWindow() == hwnd))
        if u32.GetForegroundWindow() == hwnd:
            return True
    return u32.GetForegroundWindow() == hwnd


def click_logical(hwnd, lx, ly):
    """harness click_logical: logical 800x600 -> screen via window origin, 1:1"""
    left, top, _, _ = rect_of(hwnd)
    sx, sy = left + lx, top + ly

    def _send(flags):
        inp = INPUT(type=0, mi=MOUSEINPUT(dx=sx, dy=sy, mouseData=0,
                                          dwFlags=flags, time=0, dwExtraInfo=None))
        u32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    u32.SetCursorPos(sx, sy)
    time.sleep(0.05)
    _send(0x0002)
    time.sleep(0.05)
    _send(0x0004)
    time.sleep(0.35)
    return sx, sy


def snapshot(tag, outdir):
    """capture the whole screen to a PNG using .NET (GDI GetDIBits failed here)"""
    path = os.path.join(outdir, "nav_%s.png" % tag)
    ps = (
        "Add-Type -AssemblyName System.Drawing;"
        "$b=New-Object System.Drawing.Bitmap(1706,960);"
        "$g=[System.Drawing.Graphics]::FromImage($b);"
        "$g.CopyFromScreen(0,0,0,0,(New-Object System.Drawing.Size(1706,960)));"
        "$b.Save('%s',[System.Drawing.Imaging.ImageFormat]::Png);"
        "$g.Dispose();$b.Dispose()" % path
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   capture_output=True, timeout=120)
    return path if os.path.exists(path) else None


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--launch", action="store_true")
    ap.add_argument("--pid", type=int)
    ap.add_argument("--go", action="store_true", help="actually click the NAV_CHAIN")
    ap.add_argument("--probe", action="store_true", help="report only, no clicks")
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

    w = find_main_window(pid)
    if not w:
        print("no visible main window")
        return 2
    _, hwnd, title, cw, ch = w
    left, top, ww, wh = rect_of(hwnd)
    print("hwnd=0x%X title=%r client=%dx%d rect=(%d,%d)-(%dx%d)"
          % (hwnd, title, cw, ch, left, top, ww, wh))

    trail = []
    ok = focus_foreground(hwnd, trail)
    print("focus: ok=%s trail=%s" % (ok, trail))
    print("foreground now: 0x%X (ours=0x%X)" % (u32.GetForegroundWindow(), hwnd))

    if a.probe or not a.go:
        p = snapshot("probe", a.outdir)
        print("snapshot: %s" % p)
        return 0

    for step, (name, lx, ly) in enumerate(NAV_CHAIN):
        focus_foreground(hwnd, trail)
        sx, sy = click_logical(hwnd, lx, ly)
        print("step %d %-9s logical=(%d,%d) screen=(%d,%d)"
              % (step + 1, name, lx, ly, sx, sy))
        time.sleep(1.8)
        p = snapshot("%d_%s" % (step + 1, name), a.outdir)
        print("        snapshot: %s" % os.path.basename(p) if p else "        snapshot failed")

    time.sleep(4.0)
    print("final snapshot: %s" % snapshot("final", a.outdir))
    print("\nNOTE: whether we actually got in-game is decided by the frame counter, not by")
    print("      a screenshot. Run w136_poll.py --pid %d against this process next." % pid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
