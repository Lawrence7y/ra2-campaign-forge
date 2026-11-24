#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W154 (R11 Lead live card): drive the running game without relaunching it.

Why this exists: `w144_nav3.py` always kills + relaunches gamemd, which makes it
unusable for step-by-step navigation on an already-running instance.  This tool
only *talks to* the current process:

  --state                 print mode [0xA8B238] / frame [0xA8ED84] / bullets [0xA8ED50]
  --list                  enumerate real Win32 child Buttons (class `Button`) with text+rect
  --click LX LY           click at *logical* 800x600 coords, mapped through the real
                          client rect via ClientToScreen (never assumes window origin)
  --key VK [VK...]        press keys (SendInput, scan-code based)
  --wait S                sleep after the action before re-reading state

Judgement discipline (ledger §886): clicks are judged by INTERNAL STATE only,
never by screenshots, because the menu background is an animation.
"""
import argparse
import ctypes
import struct
import sys
import time
from ctypes import wintypes as wt

FRAME = 0x00A8ED84
MODE = 0x00A8B238
BULLETS = 0x00A8ED50

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
u32.GetWindow.argtypes = [wt.HWND, wt.UINT]
u32.GetWindow.restype = wt.HWND
u32.GetClassNameA.argtypes = [wt.HWND, ctypes.c_char_p, ctypes.c_int]
u32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u32.GetClientRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u32.ClientToScreen.argtypes = [wt.HWND, ctypes.POINTER(wt.POINT)]
u32.GetWindowLongA.argtypes = [wt.HWND, ctypes.c_int]
u32.GetWindowLongA.restype = ctypes.c_long
u32.IsWindowVisible.argtypes = [wt.HWND]
u32.IsWindowVisible.restype = wt.BOOL
u32.SendMessageA.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
u32.SendMessageA.restype = ctypes.c_long
k32.GetCurrentThreadId.restype = wt.DWORD
k32.OpenProcess.restype = wt.HANDLE
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

GW_CHILD, GW_HWNDNEXT, GWL_ID = 5, 2, -12
WM_GETTEXT, WM_GETTEXTLENGTH = 0x000D, 0x000E


class MI(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", wt.DWORD),
                ("dwFlags", wt.DWORD), ("time", wt.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class KI(ctypes.Structure):
    _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class INP(ctypes.Structure):
    _fields_ = [("type", wt.DWORD), ("u", ctypes.c_byte * 32)]


u32.SendInput.argtypes = [wt.UINT, ctypes.POINTER(INP), ctypes.c_int]
u32.SendInput.restype = wt.UINT


def pid_of():
    import subprocess
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-Process gamemd -ErrorAction SilentlyContinue).Id"],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


def roots(pid_):
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


def text_of(h):
    n = u32.SendMessageA(h, WM_GETTEXTLENGTH, 0, 0)
    if not n:
        return ""
    buf = ctypes.create_string_buffer(n + 2)
    u32.SendMessageA(h, WM_GETTEXT, n + 1, ctypes.addressof(buf))
    return buf.value.decode("latin-1", "replace")


def buttons(pid_):
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
                rows.append({"hwnd": int(c), "id": u32.GetWindowLongA(c, GWL_ID),
                             "text": text_of(c), "x": r.left, "y": r.top, "w": w, "h": hh,
                             "cx": r.left + w // 2, "cy": r.top + h // 2, "depth": depth})
            walk(c, depth + 1)
            c = u32.GetWindow(c, GW_HWNDNEXT)

    for top in roots(pid_):
        walk(top)
    rows.sort(key=lambda d: (d["y"], d["x"]))
    return rows


def focus(pid_):
    tops = roots(pid_)
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


def state(h):
    def rd(va):
        b = ctypes.create_string_buffer(4)
        g = ctypes.c_size_t(0)
        ok = k32.ReadProcessMemory(h, ctypes.c_void_p(va), b, 4, ctypes.byref(g))
        return struct.unpack("<I", b.raw)[0] if ok and g.value == 4 else None
    return rd(MODE), rd(FRAME), rd(BULLETS)


def click_screen(x, y):
    u32.SetCursorPos(x, y)
    time.sleep(0.2)
    for f in (0x0002, 0x0004):
        mi = MI(dx=x, dy=y, mouseData=0, dwFlags=f, time=0, dwExtraInfo=None)
        i = INP(type=0)
        ctypes.memmove(ctypes.byref(i, 4), ctypes.byref(mi), ctypes.sizeof(mi))
        u32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INP))
        time.sleep(0.12)


def press(vk):
    scan = u32.MapVirtualKeyA(vk, 0)
    for flags in (0x0008, 0x0008 | 0x0002):  # KEYDOWN, KEYUP (scancode-based)
        ki = KI(wVk=0, wScan=scan, dwFlags=flags, time=0, dwExtraInfo=None)
        i = INP(type=1)
        ctypes.memmove(ctypes.byref(i, 4), ctypes.byref(ki), ctypes.sizeof(ki))
        u32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INP))
        time.sleep(0.08)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--click", nargs=2, type=int, metavar=("LX", "LY"))
    ap.add_argument("--click-ctrl", type=int, metavar="CTRLID")
    ap.add_argument("--key", nargs="+", type=int)
    ap.add_argument("--wait", type=float, default=2.5)
    a = ap.parse_args()

    pid_ = pid_of()
    if not pid_:
        print("gamemd not running")
        return 2
    h = k32.OpenProcess(0x0010 | 0x1000, False, pid_)

    if a.state or (not a.click and not a.list and a.click_ctrl is None and not a.key):
        print("pid=%d mode=%s frame=%s bullets=%s" % ((pid_,) + state(h)))
        return 0

    if a.click:
        g = focus(pid_)
        r = wt.RECT()
        u32.GetClientRect(g, ctypes.byref(r))
        cw, ch = r.right, r.bottom
        p = wt.POINT(0, 0)
        u32.ClientToScreen(g, ctypes.byref(p))
        lx, ly = a.click
        sx = p.x + int(round(lx * cw / 800.0))
        sy = p.y + int(round(ly * ch / 600.0))
        before = state(h)
        click_screen(sx, sy)
        time.sleep(a.wait)
        after = state(h)
        print("hwnd=0x%X client=%dx%d origin=(%d,%d) focus=%s"
              % (g, cw, ch, p.x, p.y, u32.GetForegroundWindow() == g))
        print("click logical(%d,%d) -> screen(%d,%d)" % (lx, ly, sx, sy))
        print("mode/frame/bullets %s -> %s  CHANGED=%s" % (before, after, before != after))
        return 0

    if a.click_ctrl is not None:
        rows = buttons(pid_)
        t = next((d for d in rows if d["id"] == a.click_ctrl), None)
        if not t:
            print("ctrl_id %d not found; have %s" % (a.click_ctrl, [d["id"] for d in rows]))
            return 2
        focus(pid_)
        before = state(h)
        click_screen(t["cx"], t["cy"])
        time.sleep(a.wait)
        print("clicked ctrl_id=%d text=%r centre=(%d,%d)"
              % (t["id"], t["text"], t["cx"], t["cy"]))
        print("mode/frame/bullets %s -> %s" % (before, state(h)))
        return 0

    if a.key:
        focus(pid_)
        before = state(h)
        for vk in a.key:
            press(vk)
            time.sleep(0.35)
        time.sleep(a.wait)
        print("keys %s -> mode/frame/bullets %s -> %s"
              % (a.key, before, state(h)))
        return 0

    rows = buttons(pid_)
    mode, frame, bullets = state(h)
    print("pid=%d mode=%s frame=%s bullets=%s buttons=%d"
          % (pid_, mode, frame, bullets, len(rows)))
    for i, d in enumerate(rows):
        print("%-3d hwnd=%-10s id=%-6d rect=(%4d,%4d,%3dx%-3d) centre=(%d,%d) text=%r"
              % (i, hex(d["hwnd"]), d["id"], d["x"], d["y"], d["w"], d["h"],
                 d["cx"], d["cy"], d["text"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
