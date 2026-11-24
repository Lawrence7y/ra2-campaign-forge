#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""组合输入：先强制聚焦游戏（不用 AttachThreadInput，避免卡住），再执行动作序列。
动作语法（逗号分隔，按顺序执行）：
  k<VK>          按键 (tap)，VK 十进制或 0x 十六进制
  c<X>,<Y>       左键单击 client 坐标
  r<X>,<Y>       右键单击
  m<X>,<Y>       移动鼠标
  w<X>,<Y>,<D>   在 (X,Y) 滚轮 delta D
  s<秒>          睡眠
例：--actions 'k0x24,s1.0,c400,300'
游戏须已 TOPMOST（用 focus_topmost.py）。
"""
import argparse
import ctypes
import subprocess
import sys
import time
from ctypes import wintypes as wt

u32 = ctypes.windll.user32
u32.SetForegroundWindow.argtypes = [wt.HWND]
u32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
u32.BringWindowToTop.argtypes = [wt.HWND]
u32.GetForegroundWindow.restype = wt.HWND
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.mouse_event.argtypes = [wt.DWORD, wt.DWORD, wt.DWORD, wt.DWORD, ctypes.c_size_t]
u32.keybd_event.argtypes = [wt.BYTE, wt.BYTE, wt.DWORD, ctypes.c_size_t]
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]

LEFTDOWN, LEFTUP = 0x0002, 0x0004
RIGHTDOWN, RIGHTUP = 0x0008, 0x0010
WHEEL = 0x0800
KEYUP = 0x0002


def pid_of(name="gamemd"):
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-Process %s -ErrorAction SilentlyContinue).Id" % name],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


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


def force_fg(hwnd, settle=0.35):
    u32.ShowWindow(hwnd, 9)
    u32.BringWindowToTop(hwnd)
    u32.SetForegroundWindow(hwnd)
    time.sleep(settle)
    return u32.GetForegroundWindow() == hwnd


def tap(vk, hold=0.06):
    u32.keybd_event(vk & 0xFF, 0, 0, 0)
    time.sleep(hold)
    u32.keybd_event(vk & 0xFF, 0, KEYUP, 0)
    time.sleep(0.08)


def click(x, y, right=False):
    u32.SetCursorPos(x, y)
    time.sleep(0.18)
    if right:
        u32.mouse_event(RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(0.07)
        u32.mouse_event(RIGHTUP, 0, 0, 0, 0)
    else:
        u32.mouse_event(LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.07)
        u32.mouse_event(LEFTUP, 0, 0, 0, 0)
    time.sleep(0.12)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--actions", required=True)
    ap.add_argument("--pid", type=int, default=None)
    ap.add_argument("--re-focus", action="store_true", help="每个动作前重新聚焦")
    a = ap.parse_args()
    try:
        u32.SetProcessDPIAware()
    except Exception:
        pass
    pid = a.pid or pid_of()
    if not pid:
        print("gamemd not running")
        return 2
    hwnd = game_hwnd(pid)
    if not hwnd:
        print("no window")
        return 2
    print("game hwnd=0x%X fg_before=0x%X" % (hwnd, u32.GetForegroundWindow()))
    if not force_fg(hwnd):
        print("WARN: foreground not game (0x%X)" % u32.GetForegroundWindow())
    for act in a.actions.split(","):
        act = act.strip()
        if not act:
            continue
        if a.re_focus:
            force_fg(hwnd, 0.15)
        if act.startswith("k"):
            tap(int(act[1:], 0))
            print("k %s" % act[1:])
        elif act.startswith("c") or act.startswith("r") or act.startswith("m") or act.startswith("w"):
            parts = act[1:].split(";") if ";" in act else act[1:].split("_")
            # 支持 c X;Y 或 cX Y ——统一用分号；若只有一个逗号进来会被外层拆，故用分号
            nums = [int(x, 0) for x in parts]
            if act[0] == "c":
                click(nums[0], nums[1]); print("c %s,%s" % (nums[0], nums[1]))
            elif act[0] == "r":
                click(nums[0], nums[1], True); print("r %s,%s" % (nums[0], nums[1]))
            elif act[0] == "m":
                u32.SetCursorPos(nums[0], nums[1]); print("m %s,%s" % (nums[0], nums[1]))
            elif act[0] == "w":
                u32.SetCursorPos(nums[0], nums[1]); time.sleep(0.1)
                u32.mouse_event(WHEEL, 0, 0, nums[2] & 0xFFFFFFFF, 0)
                print("w %s,%s,%s" % tuple(nums[:3]))
        elif act.startswith("s"):
            time.sleep(float(act[1:])); print("s %s" % act[1:])
        else:
            print("unknown act %r" % act)
    print("fg_after=0x%X" % u32.GetForegroundWindow())
    return 0


if __name__ == "__main__":
    sys.exit(main())
