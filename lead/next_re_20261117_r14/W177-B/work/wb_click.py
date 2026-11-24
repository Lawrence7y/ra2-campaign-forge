#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-B 输入工具：在 w177_click 的校验基础上，游戏已前台时跳过重复 force_foreground，
并在点击前做微抖动确保 WM_MOUSEMOVE 送达。保留 GetForegroundWindow 校验 + WindowFromPoint 归属校验。
不裸用 SetCursorPos：所有点击都经本函数（前台/归属双校验）。"""
import ctypes
import time
from ctypes import wintypes as wt

import w177_click as C

u32 = C.u32
LEFTDOWN, LEFTUP = C.MOUSEEVENTF_LEFTDOWN, C.MOUSEEVENTF_LEFTUP
RIGHTDOWN, RIGHTUP = C.MOUSEEVENTF_RIGHTDOWN, C.MOUSEEVENTF_RIGHTUP


def click_stable(pid, cx, cy, button="left", verify=True):
    """前置条件：游戏窗口已是前台（若否则调用一次 force_foreground）。"""
    hwnd = C.game_hwnd(pid)
    if not hwnd:
        return False, "no visible window"
    fg = u32.GetForegroundWindow()
    if fg != hwnd:
        if not C.force_foreground(hwnd):
            return False, "foreground failed"
    # 微抖动：确保游戏内部鼠标位置更新到目标点
    pt = wt.POINT(0, 0)
    u32.ClientToScreen(hwnd, ctypes.byref(pt))
    sx, sy = pt.x + cx, pt.y + cy
    u32.SetCursorPos(sx + 3, sy + 3)
    time.sleep(0.06)
    u32.SetCursorPos(sx, sy)
    time.sleep(0.10)
    if verify:
        target = u32.WindowFromPoint(wt.POINT(sx, sy))
        root = u32.GetAncestor(target, C.GA_ROOT) if target else 0
        opid = C.owner_pid(root) if root else -1
        if opid != pid:
            return False, "point not in game owner=%d" % opid
    if button == "left":
        u32.mouse_event(LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.06)
        u32.mouse_event(LEFTUP, 0, 0, 0, 0)
    else:
        u32.mouse_event(RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(0.06)
        u32.mouse_event(RIGHTUP, 0, 0, 0, 0)
    return True, "stable click (%d,%d) fg=%X" % (sx, sy, u32.GetForegroundWindow())
