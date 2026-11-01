#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""桌面锁定/输入桌面探针（只读，零发射，零写入）。§427/§428 判别辅助。"""
import ctypes
from ctypes import wintypes as wt

u = ctypes.WinDLL("user32", use_last_error=True)
u.GetForegroundWindow.restype = wt.HWND
u.GetClassNameW.restype = ctypes.c_int
u.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
u.OpenInputDesktop.restype = wt.HANDLE
u.OpenInputDesktop.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
u.GetUserObjectInformationW.restype = wt.BOOL
u.GetUserObjectInformationW.argtypes = [wt.HANDLE, ctypes.c_int, wt.LPWSTR,
                                        ctypes.c_int, ctypes.POINTER(ctypes.c_int)]

fg = u.GetForegroundWindow()
buf = ctypes.create_unicode_buffer(256)
u.GetClassNameW(fg, buf, 256)
print("foreground hwnd =", fg, "class =", repr(buf.value))

# DESKTOP_READOBJECTS=0x0001; UOI_NAME=2, UOI_FLAGS=1
h = u.OpenInputDesktop(0, False, 0x0001)
if not h:
    print("OpenInputDesktop FAILED err =", ctypes.get_last_error(),
          "(常见=权限不足，非锁定证据)")
else:
    name = ctypes.create_unicode_buffer(256)
    need = ctypes.c_int(0)
    if u.GetUserObjectInformationW(h, 2, name, 256, ctypes.byref(need)):
        print("input desktop name =", repr(name.value),
              "（'Default'=交互桌面在线；'Winlogon'=锁定界面占据）")
    flags = ctypes.c_int(0)
    if u.GetUserObjectInformationW(h, 1, ctypes.cast(ctypes.byref(flags), wt.LPWSTR),
                                   4, ctypes.byref(need)):
        pass
    ctypes.windll.user32.CloseDesktop(h)

# LogonUI / LockApp 进程（锁定界面进程）
import subprocess
r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq LogonUI.exe", "/FO", "CSV", "/NH"],
                   capture_output=True, text=True, encoding="gbk", errors="replace")
print("LogonUI:", r.stdout.strip() or r.stderr.strip())
r2 = subprocess.run(["tasklist", "/FI", "IMAGENAME eq LockApp.exe", "/FO", "CSV", "/NH"],
                    capture_output=True, text=True, encoding="gbk", errors="replace")
print("LockApp:", r2.stdout.strip() or r2.stderr.strip())
print("DPI AppliedDPI=144 ⇒ 150% 缩放（昨晚起拓扑 1707×960 逻辑=2560×1440@150% 同源）")
