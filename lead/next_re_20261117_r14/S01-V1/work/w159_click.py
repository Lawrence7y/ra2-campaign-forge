#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W159 安全合成输入：置前台 → 重测几何 → 校验目标点属于游戏窗口 → 单次点击 → 采样。

安全设计（fail-closed）：
  * 置前台失败 ⇒ **不点击**，直接退出
  * 点击前重新读取窗口几何，并把点击点换算成**屏幕坐标**后校验：该点所在窗口必须属于 gamemd
  * 每次只点一次，点完立刻采样 mode/frame，由调用方判断后果
"""
import argparse
import ctypes
import json
import sys
import time
from ctypes import wintypes as wt

import w159_probe as W

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

GA_ROOT = 2
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


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


def force_foreground(hwnd, settle=1.0):
    """把 hwnd 强行置前台。Windows 会拦 SetForegroundWindow，
    标准解法是 AttachThreadInput 到前台线程共享输入队列后再调。"""
    u32.AttachThreadInput.argtypes = [wt.DWORD, wt.DWORD, wt.BOOL]
    u32.GetWindowThreadProcessId.restype = wt.DWORD
    fg = u32.GetForegroundWindow()
    fg_tid = u32.GetWindowThreadProcessId(fg, None) if fg else 0
    my_tid = k32.GetCurrentThreadId()
    attached = False
    if fg_tid and fg_tid != my_tid:
        attached = bool(u32.AttachThreadInput(my_tid, fg_tid, True))
    try:
        u32.ShowWindow(hwnd, 9)   # SW_RESTORE
        u32.SetForegroundWindow(hwnd)
        u32.BringWindowToTop(hwnd)
        u32.SetActiveWindow(hwnd)
    finally:
        pass
    time.sleep(settle)
    ok = (u32.GetForegroundWindow() == hwnd)
    if not ok:
        # 再试一次：模拟 ALT 轻敲（解除前台锁）
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cx", type=int, required=True, help="client 坐标 x（相对客户区左上）")
    ap.add_argument("--cy", type=int, required=True)
    ap.add_argument("--settle", type=float, default=1.2)
    ap.add_argument("--post-secs", type=float, default=6.0)
    a = ap.parse_args()

    try:
        u32.SetProcessDPIAware()
    except Exception:
        pass

    pid = W.pid_of()
    if not pid:
        print("FAIL: gamemd not running"); return 2
    hwnd = game_hwnd(pid)
    if not hwnd:
        print("FAIL: no visible window for pid %d" % pid); return 2
    print("pid=%d hwnd=0x%X" % (pid, hwnd))

    # 1) 置前台（含 AttachThreadInput 破解防抢焦点）
    ok = force_foreground(hwnd, a.settle)
    fg = u32.GetForegroundWindow()
    print("force_foreground ok=%s  foreground hwnd=0x%X (game=0x%X)" % (ok, fg, hwnd))
    if fg != hwnd:
        print("FAIL: game is not foreground -> refusing to click (fail-closed)")
        return 3

    # 2) 重测几何 + 换算屏幕坐标
    r = wt.RECT()
    u32.GetWindowRect(hwnd, ctypes.byref(r))
    cl = wt.RECT()
    u32.GetClientRect(hwnd, ctypes.byref(cl))
    pt = wt.POINT(0, 0)
    u32.ClientToScreen(hwnd, ctypes.byref(pt))
    sx, sy = pt.x + a.cx, pt.y + a.cy
    print("window=(%d,%d) %dx%d  client_origin=(%d,%d)  client=%dx%d"
          % (r.left, r.top, r.right - r.left, r.bottom - r.top, pt.x, pt.y,
             cl.right - cl.left, cl.bottom - cl.top))
    print("click client=(%d,%d) -> screen=(%d,%d)" % (a.cx, a.cy, sx, sy))

    # 3) 校验该屏幕点属于游戏窗口族
    target = u32.WindowFromPoint(wt.POINT(sx, sy))
    root = u32.GetAncestor(target, GA_ROOT) if target else 0
    opid = owner_pid(root) if root else -1
    print("WindowFromPoint -> hwnd=0x%X root=0x%X owner_pid=%d (want %d)"
          % (target or 0, root or 0, opid, pid))
    if opid != pid:
        print("FAIL: point does not belong to game -> refusing to click (fail-closed)")
        return 4

    # 4) 单次左键点击
    u32.SetCursorPos(sx, sy)
    time.sleep(0.25)
    u32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.08)
    u32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    print("clicked once at screen=(%d,%d)" % (sx, sy))

    # 5) 采样后效
    m = W.Mem(pid)
    t0 = time.perf_counter()
    print("post-click sampling for %.1fs:" % a.post_secs)
    while time.perf_counter() - t0 < a.post_secs:
        print("   t=%.1fs mode=%s frame=%s bullets=%s units=%s bldg=%s abstract=%s"
              % (time.perf_counter() - t0, m.rd(W.G["mode"]), m.rd(W.G["frame"]),
                 m.rd(W.G["bullets"]), m.rd(W.G["units"]), m.rd(W.G["building"]),
                 m.rd(W.G["abstract"])))
        time.sleep(1.0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
