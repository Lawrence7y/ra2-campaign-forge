# -*- coding: utf-8 -*-
"""点击有效性实验：验证 SendInput 鼠标点击能否被 cnc-ddraw 全屏下的游戏接收。

已知（上一轮探测）：
  · 渲染面 = 窗口左上角 800x600，scale=1.0（非黑包围盒 (0,0,800,600)）
  · 主菜单按钮：單人遊戲 y≈222、網路遊戲 y≈267、網際網路 y≈310、
                動畫及製作人員 y≈355、選項 y≈390、退出遊戲 y≈557（x≈655..790）
  · 母本 NAV_CHAIN 首点 (700,218) 恰命中「單人遊戲」

本脚本测三种点击投递方式，每次点完截图看画面是否变化：
  M1 SendInput + SetCursorPos（母本 H7 同口径）
  M2 SendInput 但先把窗口 SetForegroundWindow + SetCapture 无关；改为
     附加 MOUSEEVENTF_ABSOLUTE 归一化坐标（100% 屏坐标）
  M3 PostMessage(WM_LBUTTONDOWN/UP) 直接投窗口（绕开输入队列；
     可能被 ddraw 忽略，但值得一试）
"""
import ctypes
import ctypes.wintypes as wt
import subprocess
import sys
import time
from pathlib import Path

GAME_DIR = r"D:\Project\ra2-campaign-forge\ra2youli"
GAME_EXE = GAME_DIR + r"\gamemd.exe"
OUT = Path(r"D:\Project\ra2-campaign-forge\lead\re_d13_ruling_20261112")

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wt.LONG), ("dy", wt.LONG), ("mouseData", wt.DWORD),
                ("dwFlags", wt.DWORD), ("time", wt.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class INPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]
    _anonymous_ = ("u",)
    _fields_ = [("type", wt.DWORD), ("u", _U)]


class BMI(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG),
                ("biPlanes", wt.WORD), ("biBitCount", wt.WORD),
                ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG),
                ("biClrUsed", wt.DWORD), ("biClrImportant", wt.DWORD)]


for fn, rt, at in [
    ("SetCursorPos", wt.BOOL, [ctypes.c_int, ctypes.c_int]),
    ("GetWindowDC", ctypes.c_void_p, [wt.HWND]),
    ("ReleaseDC", ctypes.c_int, [wt.HWND, ctypes.c_void_p]),
    ("GetWindowRect", wt.BOOL, [wt.HWND, ctypes.POINTER(wt.RECT)]),
    ("SetForegroundWindow", wt.BOOL, [wt.HWND]),
    ("ShowWindow", wt.BOOL, [wt.HWND, ctypes.c_int]),
    ("SetActiveWindow", wt.HWND, [wt.HWND]),
    ("PostMessageW", wt.BOOL, [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]),
    ("SendInput", wt.UINT, [wt.UINT, ctypes.POINTER(INPUT), ctypes.c_int]),
    ("GetWindowThreadProcessId", wt.DWORD, [wt.HWND, ctypes.POINTER(wt.DWORD)]),
    ("GetWindowTextLengthW", ctypes.c_int, [wt.HWND]),
    ("GetWindowTextW", ctypes.c_int, [wt.HWND, wt.LPWSTR, ctypes.c_int]),
]:
    f = getattr(user32, fn)
    f.restype = rt
    f.argtypes = at

gdi32.CreateCompatibleDC.restype = ctypes.c_void_p
gdi32.CreateCompatibleDC.argtypes = [ctypes.c_void_p]
gdi32.CreateCompatibleBitmap.restype = ctypes.c_void_p
gdi32.CreateCompatibleBitmap.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
gdi32.SelectObject.restype = ctypes.c_void_p
gdi32.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
gdi32.BitBlt.restype = wt.BOOL
gdi32.BitBlt.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                         ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                         wt.DWORD]
gdi32.GetDIBits.restype = ctypes.c_int
gdi32.GetDIBits.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wt.UINT, wt.UINT,
                            ctypes.c_void_p, ctypes.c_void_p, wt.UINT]
gdi32.DeleteObject.restype = wt.BOOL
gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
gdi32.DeleteDC.restype = wt.BOOL
gdi32.DeleteDC.argtypes = [ctypes.c_void_p]

ENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)


def find_window(pid):
    f = []

    def cb(h, l):
        q = wt.DWORD(0)
        user32.GetWindowThreadProcessId(h, ctypes.byref(q))
        if q.value == pid:
            n = user32.GetWindowTextLengthW(h)
            if n:
                b = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(h, b, n + 1)
                if "Yuri" in b.value:
                    f.append(h)
        return True

    user32.EnumWindows(ENUMPROC(cb), 0)
    return f[0] if f else None


def shot(hwnd):
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    src = user32.GetWindowDC(hwnd)
    mem = gdi32.CreateCompatibleDC(src)
    bmp = gdi32.CreateCompatibleBitmap(src, w, h)
    gdi32.SelectObject(mem, bmp)
    gdi32.BitBlt(mem, 0, 0, w, h, src, 0, 0, 0x00CC0020)
    bi = BMI()
    bi.biSize = ctypes.sizeof(BMI)
    bi.biWidth = w
    bi.biHeight = -h
    bi.biPlanes = 1
    bi.biBitCount = 32
    stride = w * 4
    buf = (ctypes.c_char * (stride * h))()
    gdi32.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(bi), 0)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem)
    user32.ReleaseDC(hwnd, src)
    return w, h, stride, bytes(buf)


def sig(raw, w, h, stride):
    """画面指纹（稀疏采样求和 + 非黑像素计数），用于判「画面是否变化」。"""
    s = 0
    nz = 0
    for yy in range(0, h, 16):
        base = yy * stride
        for xx in range(0, w, 16):
            o = base + xx * 4
            v = raw[o] + raw[o + 1] + raw[o + 2]
            s += v
            if v > 24:
                nz += 1
    return (s, nz)


def save(raw, w, h, stride, path):
    try:
        from PIL import Image
        Image.frombuffer("RGBA", (w, h), raw, "raw", "BGRA", stride, 1)\
             .convert("RGB").save(str(path))
        return True
    except Exception as e:                             # noqa: BLE001
        print("   保存失败:", e)
        return False


def m1_sendinput_screen(hwnd, x, y):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.1)
    i = INPUT()
    i.type = 0
    i.mi.dwFlags = 0x0002
    user32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INPUT))
    time.sleep(0.12)
    i.mi.dwFlags = 0x0004
    user32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INPUT))


def m2_sendinput_absolute(hwnd, x, y):
    sw = user32.GetSystemMetrics(0)
    sh = user32.GetSystemMetrics(1)
    ax = int((x * 65535) / max(1, sw - 1))
    ay = int((y * 65535) / max(1, sh - 1))
    i = INPUT()
    i.type = 0
    i.mi.dx, i.mi.dy = ax, ay
    i.mi.dwFlags = 0x0002 | 0x8000 | 0x4000       # LEFTDOWN|ABSOLUTE|MOVE
    user32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INPUT))
    time.sleep(0.12)
    i.mi.dwFlags = 0x0004 | 0x8000 | 0x4000       # LEFTUP|ABSOLUTE|MOVE
    user32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INPUT))


def m3_postmessage(hwnd, x, y):
    lp = (int(y) << 16) | (int(x) & 0xFFFF)
    user32.PostMessageW(hwnd, 0x0200, 0, lp)      # WM_MOUSEMOVE
    time.sleep(0.05)
    user32.PostMessageW(hwnd, 0x0201, 0x0001, lp)  # WM_LBUTTONDOWN (MK_LBUTTON)
    time.sleep(0.1)
    user32.PostMessageW(hwnd, 0x0202, 0, lp)       # WM_LBUTTONUP


def main():
    proc = subprocess.Popen([GAME_EXE], cwd=GAME_DIR,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("pid=%d" % proc.pid)
    results = []
    try:
        time.sleep(22)
        hwnd = find_window(proc.pid)
        print("hwnd=%r" % hwnd)
        if not hwnd:
            return 1

        w, h, stride, raw0 = shot(hwnd)
        base = sig(raw0, w, h, stride)
        print("基线画面指纹 = %s" % (base,))
        save(raw0, w, h, stride, OUT / "_click_base.png")

        # 單人遊戲 按钮中心（渲染面 800x600 内）
        TARGETS = [
            ("m1", m1_sendinput_screen, (700, 222), "單人遊戲"),
            ("m2", m2_sendinput_absolute, (700, 222), "單人遊戲"),
            ("m3", m3_postmessage, (700, 222), "單人遊戲"),
        ]
        for tag, fn, (x, y), label in TARGETS:
            print("\n-- %s: 点击 (%d,%d) = %s --" % (tag, x, y, label))
            user32.ShowWindow(hwnd, 5)
            user32.SetForegroundWindow(hwnd)
            user32.SetActiveWindow(hwnd)
            time.sleep(0.5)
            try:
                fn(hwnd, x, y)
            except Exception as e:                     # noqa: BLE001
                print("   投递异常:", e)
            time.sleep(2.5)
            w2, h2, s2, raw2 = shot(hwnd)
            cur = sig(raw2, w2, h2, s2)
            changed = (cur != base)
            print("   画面指纹=%s  变化=%s" % (cur, changed))
            save(raw2, w2, h2, s2, OUT / ("_click_%s.png" % tag))
            results.append((tag, changed, cur))
            # 若已变化，说明点有效，不必再试后面的
            if changed:
                print("   ⇒ 该投递方式有效，停止后续尝试")
                break
    finally:
        try:
            proc.terminate(); proc.wait(timeout=8)
            print("\n已终止 rc=%r" % proc.returncode)
        except Exception as e:                         # noqa: BLE001
            print("终止失败:", e)

    print("\n" + "=" * 60)
    if any(c for _, c, _ in results):
        ok = [t for t, c, _ in results if c]
        print("结论：有效投递方式 = %s" % ok)
    else:
        print("结论：三种投递方式都未改变画面 ⇒ 全屏独占下 SendInput/PostMessage 均无效")
    return 0


if __name__ == "__main__":
    sys.exit(main())
