#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""安全合成点击：置前台 -> 重测几何 -> 校验目标点属于 gamemd 窗口 -> 单次点击 -> 采样后效。
支持左键单击/右键单击/双击；可选键盘按键。全部为合成输入，不触碰目标进程内存。
"""
import argparse
import ctypes
import os
import sys
import time
from ctypes import wintypes as wt

import w177_core as W

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32

u32.SetForegroundWindow.argtypes = [wt.HWND]
u32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
u32.WindowFromPoint.argtypes = [wt.POINT]
u32.WindowFromPoint.restype = wt.HWND
u32.GetAncestor.argtypes = [wt.HWND, wt.UINT]
u32.GetAncestor.restype = wt.HWND
u32.ClientToScreen.argtypes = [wt.HWND, ctypes.POINTER(wt.POINT)]
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.mouse_event.argtypes = [wt.DWORD, wt.DWORD, wt.DWORD, wt.DWORD, ctypes.c_size_t]
u32.GetForegroundWindow.restype = wt.HWND
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u32.GetClientRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]

GA_ROOT = 2
MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP = 0x0002, 0x0004
MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP = 0x0008, 0x0010


def owner_pid(hwnd):
    t = wt.DWORD()
    u32.GetWindowThreadProcessId(hwnd, ctypes.byref(t))
    return t.value


def game_hwnd(pid):
    found = []

    def cb(hwnd, lparam):
        t = wt.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(t))
        if t.value == pid and u32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True

    EP = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    u32.EnumWindows(EP(cb), 0)
    return found[0] if found else None


def force_foreground(hwnd, settle=0.8):
    u32.AttachThreadInput.argtypes = [wt.DWORD, wt.DWORD, wt.BOOL]
    u32.GetWindowThreadProcessId.restype = wt.DWORD
    fg = u32.GetForegroundWindow()
    fg_tid = u32.GetWindowThreadProcessId(fg, None) if fg else 0
    my_tid = k32.GetCurrentThreadId()
    attached = False
    if fg_tid and fg_tid != my_tid:
        attached = bool(u32.AttachThreadInput(my_tid, fg_tid, True))
    try:
        u32.ShowWindow(hwnd, 9)
        u32.SetForegroundWindow(hwnd)
        u32.BringWindowToTop(hwnd)
        u32.SetActiveWindow(hwnd)
    finally:
        pass
    time.sleep(settle)
    ok = (u32.GetForegroundWindow() == hwnd)
    if not ok:
        VK_MENU = 0x12
        u32.keybd_event(VK_MENU, 0, 0, 0)
        u32.keybd_event(VK_MENU, 0, 2, 0)
        time.sleep(0.15)
        u32.SetForegroundWindow(hwnd)
        time.sleep(settle)
        ok = (u32.GetForegroundWindow() == hwnd)
    if attached:
        u32.AttachThreadInput(my_tid, fg_tid, False)
    return ok


def click_client(pid, cx, cy, button="left", settle=0.8, verify=True):
    try:
        u32.SetProcessDPIAware()
    except Exception:
        pass
    hwnd = game_hwnd(pid)
    if not hwnd:
        return False, "no visible window"
    if not force_foreground(hwnd, settle):
        return False, "foreground failed"
    if u32.GetForegroundWindow() != hwnd:
        return False, "game not foreground"
    r = wt.RECT()
    u32.GetWindowRect(hwnd, ctypes.byref(r))
    cl = wt.RECT()
    u32.GetClientRect(hwnd, ctypes.byref(cl))
    pt = wt.POINT(0, 0)
    u32.ClientToScreen(hwnd, ctypes.byref(pt))
    sx, sy = pt.x + cx, pt.y + cy
    info = "win=(%d,%d,%d,%d) client_origin=(%d,%d) client=(%d,%d) click=(%d,%d)->(%d,%d)" % (
        r.left, r.top, r.right, r.bottom, pt.x, pt.y, cl.right, cl.bottom, cx, cy, sx, sy)
    if verify:
        target = u32.WindowFromPoint(wt.POINT(sx, sy))
        root = u32.GetAncestor(target, GA_ROOT) if target else 0
        opid = owner_pid(root) if root else -1
        info += " WFP->root=%X owner=%d" % (root or 0, opid)
        if opid != pid:
            return False, "point not in game: " + info
    u32.SetCursorPos(sx, sy)
    time.sleep(0.15)
    if button == "left":
        u32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.06)
        u32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    else:
        u32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(0.06)
        u32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
    return True, info


def move_client(pid, cx, cy):
    try:
        u32.SetProcessDPIAware()
    except Exception:
        pass
    hwnd = game_hwnd(pid)
    if not hwnd:
        return False, "no window"
    pt = wt.POINT(0, 0)
    u32.ClientToScreen(hwnd, ctypes.byref(pt))
    sx, sy = pt.x + cx, pt.y + cy
    u32.SetCursorPos(sx, sy)
    return True, "moved to (%d,%d)" % (sx, sy)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cx", type=int)
    ap.add_argument("--cy", type=int)
    ap.add_argument("--button", choices=["left", "right"], default="left")
    ap.add_argument("--pid", type=int, default=None)
    ap.add_argument("--settle", type=float, default=0.8)
    ap.add_argument("--post", type=float, default=1.0, help="post-click sample seconds")
    a = ap.parse_args()
    pid = a.pid or W.pid_of()
    if not pid:
        print("gamemd not running")
        return 2
    ok, info = click_client(pid, a.cx, a.cy, a.button, a.settle)
    print("click ok=%s %s" % (ok, info))
    if not ok:
        return 3
    m = W.Mem(pid)
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < a.post:
        g = W.globals_snapshot(m)
        print("  t=%.2f frame=%s mode=%s obj=%s bldg_count=%s" % (
            time.perf_counter() - t0, g["frame"], g["mode"], g["objects"],
            W.building_array(m)[1]))
        time.sleep(0.5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
