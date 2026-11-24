#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""W39 step-0 standalone desktop visibility probe.

Runs in the *agent* process tree (spawned by pwsh), so it reports the desktop
that MY observation code would live on. W35 was stuck on
WinSta0\\exebox-<...> (0 windows, ImageGrab failed). W27 worked from
WinSta0\\Default. This decides whether the live test is even possible.
"""
from __future__ import annotations
import ctypes
import ctypes.wintypes as wt
import json
import sys
import traceback

u = ctypes.WinDLL("user32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)

UOI_NAME = 2
DESKTOP_READOBJECTS = 0x0001

u.GetProcessWindowStation.restype = wt.HANDLE
u.GetThreadDesktop.restype = wt.HANDLE
u.GetThreadDesktop.argtypes = [wt.DWORD]
u.OpenInputDesktop.restype = wt.HANDLE
u.OpenInputDesktop.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
u.GetUserObjectInformationW.restype = wt.BOOL
u.GetUserObjectInformationW.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                        wt.DWORD, ctypes.POINTER(wt.DWORD)]
u.CloseWindowStation.restype = wt.BOOL
u.CloseWindowStation.argtypes = [wt.HANDLE]
u.CloseDesktop.restype = wt.BOOL
u.CloseDesktop.argtypes = [wt.HANDLE]
u.EnumWindows.argtypes = [ctypes.c_void_p, wt.LPARAM]
u.EnumWindows.restype = wt.BOOL
u.EnumChildWindows.argtypes = [wt.HWND, ctypes.c_void_p, wt.LPARAM]
u.EnumChildWindows.restype = wt.BOOL
u.IsWindowVisible.argtypes = [wt.HWND]
u.IsWindowVisible.restype = wt.BOOL
u.GetWindowTextLengthW.argtypes = [wt.HWND]
u.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
u.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
k32.GetCurrentThreadId.restype = wt.DWORD

ENUM = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)


def obj_name(h):
    if not h:
        return None
    n = wt.DWORD(0)
    buf = ctypes.create_unicode_buffer(512)
    ok = u.GetUserObjectInformationW(h, UOI_NAME, buf,
                                     ctypes.sizeof(buf), ctypes.byref(n))
    return buf.value if ok else "<GetUserObjectInformationW failed err=%d>" % ctypes.get_last_error()


def wtxt(h):
    n = u.GetWindowTextLengthW(h)
    b = ctypes.create_unicode_buffer(max(n + 1, 2))
    u.GetWindowTextW(h, b, n + 1)
    return b.value


def wcls(h):
    b = ctypes.create_unicode_buffer(256)
    u.GetClassNameW(h, b, 256)
    return b.value


def main():
    r = {}
    # --- desktop names ---
    hws = u.GetProcessWindowStation()
    r["window_station"] = obj_name(hws)
    hdt = u.GetThreadDesktop(k32.GetCurrentThreadId())
    r["thread_desktop"] = obj_name(hdt)
    hin = u.OpenInputDesktop(0, False, DESKTOP_READOBJECTS)
    r["input_desktop"] = obj_name(hin) if hin else "<OpenInputDesktop returned NULL>"
    if hin:
        u.CloseDesktop(hin)

    # --- EnumWindows / EnumChildWindows ---
    tops = []

    def cb(h, _l):
        tops.append(h)
        return True

    u.EnumWindows(ENUM(cb), 0)
    r["enum_windows_total"] = len(tops)
    vis = [h for h in tops if u.IsWindowVisible(h)]
    r["enum_windows_visible"] = len(vis)
    r["sample_tops"] = [{"hwnd": int(h), "class": wcls(h), "title": wtxt(h)}
                        for h in tops[:12]]
    # exercise EnumChildWindows on the first few visible tops
    child_total = 0
    child_sample = []
    for h in vis[:8]:
        kids = []

        def ccb(kk, _l):
            kids.append(kk)
            return True
        u.EnumChildWindows(h, ENUM(ccb), 0)
        child_total += len(kids)
        for kk in kids[:5]:
            child_sample.append({"parent": int(h), "hwnd": int(kk),
                                 "class": wcls(kk), "title": wtxt(kk)})
    r["enum_child_windows_total_on_first8_visible"] = child_total
    r["child_sample"] = child_sample[:12]

    # --- screenshot capability ---
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        r["imagegrab"] = "OK"
        r["imagegrab_size"] = [img.width, img.height]
        # non-black pixel sanity (optional, cheap): sample a few pixels
        try:
            px = [img.getpixel((img.width // 4 * i, img.height // 2))
                  for i in (1, 2, 3)]
            r["imagegrab_sample_pixels"] = [list(map(int, p)) if isinstance(p, tuple)
                                            else int(p) for p in px]
        except Exception as e:
            r["imagegrab_pixel_err"] = repr(e)
    except Exception as e:
        r["imagegrab"] = "FAILED: %s" % repr(e)
        r["imagegrab_tb"] = traceback.format_exc()[-800:]

    # --- verdict ---
    enum_ok = (r["enum_windows_total"] >= 1)
    grab_ok = (r["imagegrab"] == "OK")
    r["precheck_enumwindows_ge1"] = enum_ok
    r["precheck_imagegrab_ok"] = grab_ok
    r["precheck_pass"] = bool(enum_ok and grab_ok)
    return r


if __name__ == "__main__":
    try:
        res = main()
    except Exception as e:
        res = {"fatal": repr(e), "tb": traceback.format_exc()[-1200:],
               "precheck_pass": False}
    out = sys.argv[1] if len(sys.argv) > 1 else None
    s = json.dumps(res, ensure_ascii=False, indent=2)
    print(s)
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(s + "\n")
