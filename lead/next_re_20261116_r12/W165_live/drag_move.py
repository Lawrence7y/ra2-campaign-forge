"""拖拽框选 + 右键移动，观察 moving 是否上升。只读内存 + 合成输入。"""
import ctypes
import time
from ctypes import wintypes as wt

import w165_probe as W

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
u32.SetForegroundWindow.argtypes = [wt.HWND]
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.mouse_event.argtypes = [wt.DWORD, wt.DWORD, wt.DWORD, wt.DWORD, ctypes.c_size_t]
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u32.AttachThreadInput.argtypes = [wt.DWORD, wt.DWORD, wt.BOOL]

LDOWN, LUP, RDOWN, RUP = 0x0002, 0x0004, 0x0008, 0x0010


def hwnd_of(pid):
    found = []

    def cb(h, l):
        t = wt.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(t))
        if t.value == pid and u32.IsWindowVisible(h):
            found.append(h)
        return True

    EP = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    u32.EnumWindows(EP(cb), 0)
    return found[0] if found else None


def main():
    pid = W.pid_of()
    m = W.Mem(pid)
    h = hwnd_of(pid)
    fg = u32.GetForegroundWindow()
    fgt = u32.GetWindowThreadProcessId(fg, None)
    myt = k32.GetCurrentThreadId()
    attached = False
    if fgt and fgt != myt:
        u32.AttachThreadInput(myt, fgt, True)
        attached = True
    u32.ShowWindow(h, 9)
    u32.SetForegroundWindow(h)
    u32.BringWindowToTop(h)
    time.sleep(0.6)
    if attached:
        u32.AttachThreadInput(myt, fgt, False)
    print("fg match: %s" % (u32.GetForegroundWindow() == h))

    def snap(label):
        r = W.snapshot(m)
        print("  %-20s frame=%-5s objects=%-3s lc=%-3s loco=%-3s tgt=%-3s moving=%-3s"
              % (label, r["frame"], r["objects"], r["lc_count"], r["with_loco"],
                 r["has_target"], r["moving"]))
        return r

    snap("before")

    # 拖拽框选
    u32.SetCursorPos(560, 150)
    time.sleep(0.15)
    u32.mouse_event(LDOWN, 0, 0, 0, 0)
    time.sleep(0.15)
    for k in range(1, 9):
        u32.SetCursorPos(560 + k * 22, 150 + k * 40)
        time.sleep(0.04)
    time.sleep(0.15)
    u32.mouse_event(LUP, 0, 0, 0, 0)
    time.sleep(0.6)
    snap("after drag-select")

    # 右键移动
    u32.SetCursorPos(200, 480)
    time.sleep(0.1)
    u32.mouse_event(RDOWN, 0, 0, 0, 0)
    time.sleep(0.06)
    u32.mouse_event(RUP, 0, 0, 0, 0)
    time.sleep(0.6)
    peak = 0
    for i in range(10):
        r = snap("move t+%.1fs" % ((i + 1) * 0.9))
        peak = max(peak, r["moving"])
        time.sleep(0.9)
    print("  peak moving = %d" % peak)


if __name__ == "__main__":
    main()
