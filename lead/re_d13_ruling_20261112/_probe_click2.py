# -*- coding: utf-8 -*-
"""点击有效性严谨判定：排除背景动画干扰，并检查 cnc-ddraw 的鼠标坐标映射。

上一轮的失败教训：
  · 用「全画面稀疏指纹」判变化是错的 —— 主菜单雷达背景是**动画**，
    指纹每帧都变（308877 → 324977 就是动画，不是菜单切换）。
  · 正确判据：只看**按钮栏区域**（x 650..790, y 195..420）的像素是否变化，
    且要求变化幅度显著（按钮按下/菜单切换会大改这一区域）。

本脚本：
  1. 取按钮栏基线
  2. 点击 (700,222)「單人遊戲」
  3. 取按钮栏新图，比较差异像素数与差异幅度
  4. 另做「hover 探测」：把鼠标停在按钮上不动，看按钮是否高亮（RA2 按钮 hover 会亮）
     —— 这能单独证明「游戏是否收到鼠标位置」
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


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wt.LONG), ("dy", wt.LONG), ("mouseData", wt.DWORD),
                ("dwFlags", wt.DWORD), ("time", wt.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


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
    ("GetCursorPos", wt.BOOL, [ctypes.POINTER(wt.POINT)]),
    ("GetWindowDC", ctypes.c_void_p, [wt.HWND]),
    ("ReleaseDC", ctypes.c_int, [wt.HWND, ctypes.c_void_p]),
    ("GetWindowRect", wt.BOOL, [wt.HWND, ctypes.POINTER(wt.RECT)]),
    ("SetForegroundWindow", wt.BOOL, [wt.HWND]),
    ("ShowWindow", wt.BOOL, [wt.HWND, ctypes.c_int]),
    ("SendInput", wt.UINT, [wt.UINT, ctypes.POINTER(INPUT), ctypes.c_int]),
    ("GetWindowThreadProcessId", wt.DWORD, [wt.HWND, ctypes.POINTER(wt.DWORD)]),
    ("GetWindowTextLengthW", ctypes.c_int, [wt.HWND]),
    ("GetWindowTextW", ctypes.c_int, [wt.HWND, wt.LPWSTR, ctypes.c_int]),
    ("GetForegroundWindow", wt.HWND, []),
    ("ClientToScreen", wt.BOOL, [wt.HWND, ctypes.POINTER(wt.POINT)]),
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
                         ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, wt.DWORD]
gdi32.GetDIBits.restype = ctypes.c_int
gdi32.GetDIBits.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wt.UINT, wt.UINT,
                            ctypes.c_void_p, ctypes.c_void_p, wt.UINT]
gdi32.DeleteObject.restype = wt.BOOL
gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
gdi32.DeleteDC.restype = wt.BOOL
gdi32.DeleteDC.argtypes = [ctypes.c_void_p]

ENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

BUTTON_REGION = (650, 195, 141, 230)      # x, y, w, h —— 按钮栏


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


def region_sig(raw, w, h, stride, region):
    x0, y0, rw, rh = region
    s = 0
    vals = []
    for yy in range(y0, min(y0 + rh, h)):
        base = yy * stride
        for xx in range(x0, min(x0 + rw, w)):
            o = base + xx * 4
            v = raw[o] + raw[o + 1] + raw[o + 2]
            s += v
            vals.append(v)
    return s, vals


def diff_count(v1, v2, thresh=24):
    n = 0
    big = 0
    for a, b in zip(v1, v2):
        d = abs(a - b)
        if d > 8:
            n += 1
        if d > thresh:
            big += 1
    return n, big


def click(x, y):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.12)
    i = INPUT()
    i.type = 0
    i.mi.dwFlags = 0x0002
    user32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INPUT))
    time.sleep(0.15)
    i.mi.dwFlags = 0x0004
    user32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INPUT))


def save(raw, w, h, stride, path):
    try:
        from PIL import Image
        Image.frombuffer("RGBA", (w, h), raw, "raw", "BGRA", stride, 1)\
             .convert("RGB").save(str(path))
    except Exception as e:                             # noqa: BLE001
        print("   保存失败:", e)


def main():
    proc = subprocess.Popen([GAME_EXE], cwd=GAME_DIR,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("pid=%d" % proc.pid)
    try:
        time.sleep(22)
        hwnd = find_window(proc.pid)
        print("hwnd=%r" % hwnd)
        if not hwnd:
            return 1
        user32.ShowWindow(hwnd, 5)
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.6)

        fg = user32.GetForegroundWindow()
        print("前台窗口 == 游戏窗口 ? %s (fg=%r hwnd=%r)" % (fg == hwnd, fg, hwnd))

        # ---- 1. hover 探测：鼠标移开 vs 停在按钮上，比较按钮栏 ----
        print("\n--- hover 探测（证明游戏是否收到鼠标位置）--")
        user32.SetCursorPos(200, 700)      # 移到画面外（黑区）
        time.sleep(0.8)
        w, h, s, rawA = shot(hwnd)
        _, vA = region_sig(rawA, w, h, s, BUTTON_REGION)
        user32.SetCursorPos(700, 222)      # 停在「單人遊戲」上
        time.sleep(0.8)
        w, h, s, rawB = shot(hwnd)
        _, vB = region_sig(rawB, w, h, s, BUTTON_REGION)
        n, big = diff_count(vA, vB)
        print("  按钮栏差异像素=%d（显著=%d）" % (n, big))
        hover_works = big > 200
        print("  ⇒ 游戏收到鼠标 hover: %s" % hover_works)
        cp = wt.POINT()
        user32.GetCursorPos(ctypes.byref(cp))
        print("  实际光标位置=(%d,%d)" % (cp.x, cp.y))
        save(rawB, w, h, s, OUT / "_hover_on_button.png")

        # ---- 2. 点击判定（只看按钮栏 + 等更久）----
        print("\n--- 点击 (700,222) 單人遊戲，用按钮栏判据 ---")
        click(700, 222)
        time.sleep(1.5)                     # 等菜单切换动画
        w, h, s, rawC = shot(hwnd)
        _, vC = region_sig(rawC, w, h, s, BUTTON_REGION)
        n2, big2 = diff_count(vB, vC)
        print("  点击后按钮栏差异像素=%d（显著=%d）" % (n2, big2))
        clicked = big2 > 200
        print("  ⇒ 菜单已切换: %s" % clicked)
        save(rawC, w, h, s, OUT / "_after_click_menu.png")

        if not clicked:
            print("\n  再等 3s 复看（排除慢刷新）...")
            time.sleep(3.0)
            w, h, s, rawD = shot(hwnd)
            _, vD = region_sig(rawD, w, h, s, BUTTON_REGION)
            n3, big3 = diff_count(vB, vD)
            print("  再等后按钮栏差异像素=%d（显著=%d）" % (n3, big3))
            save(rawD, w, h, s, OUT / "_after_click_menu2.png")
    finally:
        try:
            proc.terminate(); proc.wait(timeout=8)
            print("\n已终止 rc=%r" % proc.returncode)
        except Exception as e:                         # noqa: BLE001
            print("终止失败:", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
