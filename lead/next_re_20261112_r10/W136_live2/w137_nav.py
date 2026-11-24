#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W137: minimal screen-state navigator for gamemd.exe (reuses the harness's
proven red-button signature method, WITHOUT importing the 8.8k-line trip script).

Why this exists: the per-frame analysis (ledger §881-§883) can only be measured
in-game, and `-ATTRACT` does not start a skirmish (verified live: frame counter
stayed 0 for 70 s).  The project's own harness solves navigation with:
  - a screenshot of the game window,
  - "red button band" detection on the right strip (sidebar/game buttons),
  - matching those bands against a small signature table,
  - clicking a computed point.
Those constants were read from `goal1_harness8_20261031/qc151_trip.harness8_v4.py`
(SCREEN_SIG at char ~116004; _red_button_centers / _sig_match).

This script implements exactly that, plus a click, and nothing else.
READ-ONLY on the game except synthetic mouse input (SendInput).

Usage:
    python -X utf8 w137_nav.py --pid 1234 --probe
    python -X utf8 w137_nav.py --pid 1234 --to-skirmish
"""
import argparse
import ctypes
import io
import os
import subprocess
import sys
import time
from ctypes import wintypes as wt

# ---- signatures copied verbatim from the harness (logic 600-high band centres) ----
SCREEN_SIG = {
    "mainmenu":       {"present": [220, 262, 304, 346, 388, 556], "absent": []},
    "sp_submenu":     {"present": [220, 262, 304, 556],           "absent": [346, 388]},
    "skirmish_setup": {"present": [262, 304, 556],                "absent": [220]},
}
TOL = 3

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
user32.GetDC.restype = wt.HDC
user32.ReleaseDC.argtypes = [wt.HWND, wt.HDC]
gdi32.CreateCompatibleDC.restype = wt.HDC
gdi32.CreateCompatibleBitmap.restype = wt.HBITMAP
gdi32.GetDIBits.argtypes = [wt.HDC, wt.HBITMAP, wt.UINT, wt.UINT,
                            ctypes.c_void_p, ctypes.c_void_p, wt.UINT]
gdi32.SelectObject.argtypes = [wt.HDC, wt.HGDIOBJ]
gdi32.SelectObject.restype = wt.HGDIOBJ
gdi32.DeleteObject.argtypes = [wt.HGDIOBJ]
gdi32.DeleteDC.argtypes = [wt.HDC]
gdi32.CreateCompatibleBitmap.argtypes = [wt.HDC, ctypes.c_int, ctypes.c_int]
gdi32.BitBlt.argtypes = [wt.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                         wt.HDC, ctypes.c_int, ctypes.c_int, wt.DWORD]
user32.PrintWindow.argtypes = [wt.HWND, wt.HDC, wt.UINT]
user32.EnumWindows.argtypes = [ctypes.c_void_p, wt.LPARAM]
user32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
user32.GetClientRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
user32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
user32.IsWindowVisible.argtypes = [wt.HWND]
user32.SetForegroundWindow.argtypes = [wt.HWND]
user32.mouse_event.argtypes = [wt.DWORD, wt.DWORD, wt.DWORD, wt.DWORD, ctypes.c_size_t]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", ctypes.c_long),
                ("biHeight", ctypes.c_long), ("biPlanes", wt.WORD),
                ("biBitCount", wt.WORD), ("biCompression", wt.DWORD),
                ("biSizeImage", wt.DWORD), ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wt.DWORD),
                ("biClrImportant", wt.DWORD)]


def find_window(pid):
    """return (hwnd, w, h) of the largest top-level window owned by pid"""
    best = None
    EnumProc = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

    def cb(hwnd, lp):
        nonlocal best
        tid = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(tid))
        if tid.value != pid:
            return True
        if not user32.IsWindowVisible(hwnd):
            return True
        r = wt.RECT()
        if not user32.GetClientRect(hwnd, ctypes.byref(r)):
            return True
        w, h = r.right - r.left, r.bottom - r.top
        if w < 200 or h < 150:
            return True
        if best is None or w * h > best[1] * best[2]:
            best = (hwnd, w, h)
        return True

    user32.EnumWindows(EnumProc(cb), 0)
    return best


def grab(hwnd, w, h):
    """capture the window client area; returns list of rows of (r,g,b) or None"""
    hdc = user32.GetDC(hwnd)
    if not hdc:
        return None
    mdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mdc, bmp)
    ok = user32.PrintWindow(hwnd, mdc, 0) if hasattr(user32, "PrintWindow") else 0
    if not ok:
        gdi32.BitBlt(mdc, 0, 0, w, h, hdc, 0, 0, 0x00CC0020)
    bi = BITMAPINFOHEADER()
    bi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bi.biWidth = w
    bi.biHeight = -h            # top-down
    bi.biPlanes = 1
    bi.biBitCount = 24
    bi.biCompression = 0
    buf = ctypes.create_string_buffer(w * h * 3)
    got = gdi32.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bi), 0)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mdc)
    user32.ReleaseDC(hwnd, hdc)
    if not got:
        return None
    return buf.raw, w, h


def red_centers(raw, w, h):
    """replicate _red_button_centers: right strip x>=0.80w, red mask, band centres
    scaled to a logic height of 600."""
    stride = w * 3
    x0 = int(w * 0.80)
    centers = []
    inb = False
    y0 = 0
    min_h = max(4, int(h * 0.010))
    for y in range(h):
        base = y * stride
        cnt = 0
        for x in range(x0, w):
            i = base + x * 3
            b = raw[i]
            g = raw[i + 1]
            r = raw[i + 2]
            if r > 140 and r > g + 50 and r > b + 50:
                cnt += 1
        frac = cnt / float(w - x0) if w > x0 else 0.0
        v = frac > 0.25
        if v and not inb:
            inb, y0 = True, y
        elif not v and inb:
            inb = False
            if y - y0 >= min_h:
                centers.append(int(round((y0 + y - 1) / 2.0 / h * 600)))
    return centers


def sig_match(got, want, absent):
    if absent and any(any(abs(g - wv) <= TOL for g in got) for wv in absent):
        return False
    return (len(got) >= len(want)
            and all(any(abs(g - wv) <= TOL for g in got) for wv in want))


def classify(centers):
    hits = [name for name, sig in SCREEN_SIG.items()
            if sig_match(centers, sig["present"], sig.get("absent", []))]
    return hits


def click_logical(hwnd, lx, ly, w, h):
    """click a point given in logic (600-high) coordinates"""
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    sx = r.left + int(round(lx / 800.0 * w))
    sy = r.top + int(round(ly / 600.0 * h))
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.15)
    user32.SetCursorPos(sx, sy)
    time.sleep(0.08)
    user32.mouse_event(0x0002, 0, 0, 0, 0)   # LEFTDOWN
    time.sleep(0.05)
    user32.mouse_event(0x0004, 0, 0, 0, 0)   # LEFTUP
    return sx, sy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, required=True)
    ap.add_argument("--probe", action="store_true", help="just report what we see")
    ap.add_argument("--to-skirmish", action="store_true")
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--rounds", type=int, default=40)
    a = ap.parse_args()

    info = find_window(a.pid)
    if not info:
        print("no visible window for pid %d" % a.pid)
        return 2
    hwnd, w, h = info
    print("window hwnd=0x%X  client=%dx%d" % (hwnd, w, h))

    hist = []
    for r in range(a.rounds):
        g = grab(hwnd, w, h)
        if not g:
            print("capture failed")
            return 2
        raw, ww, hh = g
        centers = red_centers(raw, ww, hh)
        hits = classify(centers)
        hist.append((r, centers, hits))
        print("round %2d  centers=%-32s -> %s" % (r, centers, hits or "UNKNOWN"))
        if a.probe:
            break
        if "skirmish_setup" in hits:
            print("REACHED skirmish_setup")
            break
        if "mainmenu" in hits:
            # main menu: 6 bands 220/262/304/346/388/556. Band 346 = "Single Player"? unknown;
            # click the 4th band centre (index 3) which the harness maps as its first nav click.
            target = centers[3] if len(centers) > 3 else centers[0]
            print("  click mainmenu band y=%d" % target)
            click_logical(hwnd, 400, target, ww, hh)
        elif "sp_submenu" in hits:
            target = centers[0]
            print("  click sp_submenu band y=%d" % target)
            click_logical(hwnd, 400, target, ww, hh)
        time.sleep(1.2)

    with io.open(os.path.join(a.outdir, "nav_hist.txt"), "w", encoding="utf-8") as f:
        for r, c, hh2 in hist:
            f.write("%d\t%s\t%s\n" % (r, c, hh2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
