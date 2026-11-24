#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""W20 一次性前台修复工具（隐藏启动）：把 gamemd(pid=ARGV1) 的
"Yuri's Revenge" 主窗口重新置前（与探针 force_foreground 同款手势）。
背景：06:23:45 手工分离观察者时 cmd 控制台弹窗抢前台（误干预 #1），
游戏失去前台但帧循环仍在 31.26 计数/s 全速推进。本工具=误干预修复 #2，
结果写 fg_restore.json（W20_combat 写域内）。只动前台归属，不向游戏发任何按键。
"""
import ctypes
import ctypes.wintypes as wt
import json
import sys
import time
from pathlib import Path

u = ctypes.WinDLL("user32", use_last_error=True)
for fn, rt, at in [
    ("EnumWindows", wt.BOOL, [ctypes.c_void_p, wt.LPARAM]),
    ("GetWindowThreadProcessId", wt.DWORD, [wt.HWND, ctypes.POINTER(wt.DWORD)]),
    ("GetClassNameW", ctypes.c_int, [wt.HWND, wt.LPWSTR, ctypes.c_int]),
    ("IsWindowVisible", wt.BOOL, [wt.HWND]),
    ("SetForegroundWindow", wt.BOOL, [wt.HWND]),
    ("ShowWindow", wt.BOOL, [wt.HWND, ctypes.c_int]),
    ("BringWindowToTop", wt.BOOL, [wt.HWND]),
    ("AllowSetForegroundWindow", wt.BOOL, [wt.DWORD]),
    ("keybd_event", None, [ctypes.c_ubyte, ctypes.c_ubyte, wt.DWORD,
                           ctypes.c_size_t]),
    ("GetForegroundWindow", wt.HWND, []),
]:
    f = getattr(u, fn)
    f.restype = rt
    f.argtypes = at
ENUM = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

PID = int(sys.argv[1])
OUTP = Path(sys.argv[2])

hits = []


def cb(h, l):
    q = wt.DWORD(0)
    u.GetWindowThreadProcessId(h, ctypes.byref(q))
    if q.value == PID:
        b = ctypes.create_unicode_buffer(256)
        u.GetClassNameW(h, b, 256)
        if b.value == "Yuri's Revenge" and u.IsWindowVisible(h):
            hits.append(int(h))
    return True


u.EnumWindows(ENUM(cb), 0)
res = {"t_utc_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
       "pid": PID, "hits": hits}
if hits:
    hwnd = hits[0]
    try:
        u.AllowSetForegroundWindow(0xFFFFFFFF)
    except Exception:
        pass
    u.keybd_event(0x12, 0, 0, 0)
    try:
        u.ShowWindow(hwnd, 9)
        u.BringWindowToTop(hwnd)
        u.SetForegroundWindow(hwnd)
    finally:
        u.keybd_event(0x12, 0, 0x0002, 0)
    time.sleep(0.2)
    fg = u.GetForegroundWindow()
    q = wt.DWORD(0)
    u.GetWindowThreadProcessId(fg, ctypes.byref(q))
    res["fg_after_pid"] = int(q.value)
    res["fg_is_game"] = int(q.value) == PID
else:
    res["fg_is_game"] = False
    res["note"] = "no visible Yuri's Revenge window found"
OUTP.write_text(json.dumps(res, ensure_ascii=False, indent=1),
                encoding="utf-8")
print(json.dumps(res))
