# -*- coding: utf-8 -*-
"""渲染面探测实验：不动任何配置文件，靠运行时手段解出 800x600 渲染面的真实位置。

三条探测路径（都不改 ddraw.ini / ra2md.ini）：
  P1 客户区探测    GetClientRect vs GetWindowRect —— 若 cnc-ddraw 把游戏画进客户区，
                   客户区就是渲染面；从客户区 Origin 起做映射。
  P2 Enter 切窗口  ddraw.ini 的 keytogglefullscreen=0x0D ⇒ 运行时按 Enter
                   让 cnc-ddraw 切成窗口模式，窗口尺寸即真实渲染尺寸。
  P3 只截游戏窗口  BitBlt 用 GetWindowDC(hwnd) 而**不是屏幕 DC**，
                   这样不会把桌面/其它窗口算进来（修上一轮 bbox 污染桌面的问题）。

每种探测都打印：窗口 rect、客户区 rect、非黑包围盒、推断出的 origin/scale。
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
user32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
user32.GetClientRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
user32.ClientToScreen.argtypes = [wt.HWND, ctypes.POINTER(wt.POINT)]
user32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
user32.GetWindowTextLengthW.argtypes = [wt.HWND]
user32.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, wt.INT]
# ★ HDC 必须用 c_void_p：GetWindowDC 返回值高位为 1，用 wt.HDC(int) 会 OverflowError
gdi32.CreateCompatibleDC.restype = ctypes.c_void_p
gdi32.CreateCompatibleDC.argtypes = [ctypes.c_void_p]
gdi32.CreateCompatibleBitmap.restype = ctypes.c_void_p
gdi32.CreateCompatibleBitmap.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
gdi32.SelectObject.restype = ctypes.c_void_p
gdi32.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
gdi32.BitBlt.restype = wt.BOOL
gdi32.BitBlt.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                         ctypes.c_int, ctypes.c_int, ctypes.c_void_p,
                         ctypes.c_int, ctypes.c_int, wt.DWORD]
gdi32.GetDIBits.restype = ctypes.c_int
gdi32.GetDIBits.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wt.UINT, wt.UINT,
                            ctypes.c_void_p, ctypes.c_void_p, wt.UINT]
gdi32.DeleteObject.restype = wt.BOOL
gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
gdi32.DeleteDC.restype = wt.BOOL
gdi32.DeleteDC.argtypes = [ctypes.c_void_p]
user32.GetWindowDC.restype = ctypes.c_void_p
user32.GetWindowDC.argtypes = [wt.HWND]
user32.GetDC.restype = ctypes.c_void_p
user32.GetDC.argtypes = [wt.HWND]
user32.ReleaseDC.restype = ctypes.c_int
user32.ReleaseDC.argtypes = [wt.HWND, ctypes.c_void_p]

ENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)


class BMI(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG),
                ("biPlanes", wt.WORD), ("biBitCount", wt.WORD),
                ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG),
                ("biClrUsed", wt.DWORD), ("biClrImportant", wt.DWORD)]


def find_window(pid):
    found = []

    def cb(h, l):
        q = wt.DWORD(0)
        user32.GetWindowThreadProcessId(h, ctypes.byref(q))
        if q.value == pid:
            n = user32.GetWindowTextLengthW(h)
            if n:
                b = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(h, b, n + 1)
                if "Yuri" in b.value:
                    found.append(h)
        return True

    user32.EnumWindows(ENUMPROC(cb), 0)
    return found[0] if found else None


def grab(hwnd, use_window_dc=True):
    """截取指定 hwnd。use_window_dc=True 走 GetWindowDC（**不碰桌面**）。"""
    rc = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rc))
    w, h = rc.right - rc.left, rc.bottom - rc.top
    if use_window_dc:
        hdcS = user32.GetWindowDC(hwnd)
        srcx, srcy = 0, 0
    else:
        hdcS = user32.GetDC(0)
        srcx, srcy = rc.left, rc.top
    hdcM = gdi32.CreateCompatibleDC(hdcS)
    bmp = gdi32.CreateCompatibleBitmap(hdcS, w, h)
    gdi32.SelectObject(hdcM, bmp)
    gdi32.BitBlt(hdcM, 0, 0, w, h, hdcS, srcx, srcy, 0x00CC0020)
    bi = BMI()
    bi.biSize = ctypes.sizeof(BMI)
    bi.biWidth = w
    bi.biHeight = -h
    bi.biPlanes = 1
    bi.biBitCount = 32
    bi.biCompression = 0
    stride = w * 4
    buf = (ctypes.c_char * (stride * h))()
    gdi32.GetDIBits(hdcM, bmp, 0, h, buf, ctypes.byref(bi), 0)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(hdcM)
    if use_window_dc:
        user32.ReleaseDC(hwnd, hdcS)
    else:
        user32.ReleaseDC(None, hdcS)
    return w, h, stride, bytes(buf)


def bbox_nonblack(w, h, stride, raw, thresh=8, step=1):
    """非黑包围盒（可 step 抽样加速）。"""
    minx, miny, maxx, maxy = w, h, -1, -1
    for yy in range(0, h, step):
        base = yy * stride
        for xx in range(0, w, step):
            o = base + xx * 4
            if raw[o] > thresh or raw[o + 1] > thresh or raw[o + 2] > thresh:
                if xx < minx:
                    minx = xx
                if xx > maxx:
                    maxx = xx
                if yy < miny:
                    miny = yy
                if yy > maxy:
                    maxy = yy
    if maxx < 0:
        return None
    return (minx, miny, maxx + step - minx, maxy + step - miny)   # x,y,w,h


def send_key(vk, up=False):
    inp = INPUT()
    inp.type = 1                                  # INPUT_KEYBOARD
    inp.ki.wVk = vk
    inp.ki.dwFlags = 0x0002 if up else 0           # KEYEVENTF_KEYUP
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class INPUT(ctypes.Structure):
    class _U(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]
    _anonymous_ = ("u",)
    _fields_ = [("type", wt.DWORD), ("u", _U)]


def main():
    print("=" * 78)
    print("渲染面探测实验（不改任何配置）")
    print("=" * 78)

    proc = subprocess.Popen([GAME_EXE], cwd=GAME_DIR,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("pid=%d" % proc.pid)
    try:
        time.sleep(22)
        hwnd = find_window(proc.pid)
        print("hwnd=%r" % hwnd)
        if not hwnd:
            print("!! 找不到窗口")
            return 1

        # ---------- P1 客户区 ----------
        print("\n--- P1 客户区 / 窗口 rect ---")
        wr, cr = wt.RECT(), wt.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(wr))
        user32.GetClientRect(hwnd, ctypes.byref(cr))
        ww, wh = wr.right - wr.left, wr.bottom - wr.top
        cw, ch = cr.right - cr.left, cr.bottom - cr.top
        print("  窗口 rect=(%d,%d,%dx%d)" % (wr.left, wr.top, ww, wh))
        print("  客户区=%dx%d" % (cw, ch))
        pt = wt.POINT(0, 0)
        user32.ClientToScreen(hwnd, ctypes.byref(pt))
        print("  客户区屏幕原点=(%d,%d)" % (pt.x, pt.y))

        # ---------- P3 只截窗口（修 bbox 污染桌面） ----------
        print("\n--- P3 只用 GetWindowDC 截本窗口，求非黑包围盒 ---")
        w, h, stride, raw = grab(hwnd, use_window_dc=True)
        bb = bbox_nonblack(w, h, stride, raw, step=2)
        print("  截图 %dx%d  非黑包围盒(x,y,w,h)=%s" % (w, h, bb))
        if bb:
            bx, by, bw, bh = bb
            print("  若渲染面=800x600 ⇒ scale=(%.4f, %.4f)"
                  % (bw / 800.0, bh / 600.0))
            # 保存一张
            save_png(raw, w, h, stride, OUT / "_probe_P3_windowdc.png")

        # ---------- P2 Enter 切窗口 ----------
        print("\n--- P2 发送 Enter（keytogglefullscreen=0x0D）尝试切窗口 ---")
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.4)
        send_key(0x0D)                 # VK_RETURN down
        time.sleep(0.05)
        send_key(0x0D, up=True)
        time.sleep(3.0)
        wr2, cr2 = wt.RECT(), wt.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(wr2))
        user32.GetClientRect(hwnd, ctypes.byref(cr2))
        print("  切换后窗口 rect=(%d,%d,%dx%d)"
              % (wr2.left, wr2.top, wr2.right - wr2.left, wr2.bottom - wr2.top))
        print("  切换后客户区=%dx%d" % (cr2.right - cr2.left, cr2.bottom - cr2.top))
        w2, h2, s2, raw2 = grab(hwnd, use_window_dc=True)
        bb2 = bbox_nonblack(w2, h2, s2, raw2, step=2)
        print("  切换后截图 %dx%d 非黑包围盒=%s" % (w2, h2, bb2))
        if bb2:
            bx, by, bw, bh = bb2
            print("  若渲染面=800x600 ⇒ scale=(%.4f, %.4f)  origin=(%d,%d)"
                  % (bw / 800.0, bh / 600.0, bx, by))
            save_png(raw2, w2, h2, s2, OUT / "_probe_P2_after_enter.png")
    finally:
        try:
            proc.terminate(); proc.wait(timeout=8)
            print("\n已终止 rc=%r" % proc.returncode)
        except Exception as e:                    # noqa: BLE001
            print("终止失败: %s" % e)
    return 0


def save_png(raw, w, h, stride, path):
    """写 32bpp BMP（BGRA→BGR 由 PIL 代劳），再用 PIL 存 PNG。"""
    try:
        from PIL import Image
        im = Image.frombuffer("RGBA", (w, h), raw, "raw", "BGRA", stride, 1)
        im = im.convert("RGB")
        im.save(str(path))
        print("  已保存 %s (%dx%d)" % (path.name, w, h))
    except Exception as e:                        # noqa: BLE001
        print("  保存失败: %s" % e)


if __name__ == "__main__":
    sys.exit(main())
