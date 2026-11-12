# -*- coding: utf-8 -*-
"""B 路第 3 轮：找出真正接收鼠标输入的窗口 + 补测上轮未执行的投递方式。

上轮两个缺口：
  G1 `_probe_click.py` 里 M2（绝对坐标 SendInput）与 M3（PostMessage）**从未执行**
     —— 因为 M1「命中」就 break，而那次命中是背景动画造成的假阳性。
  G2 我一直用 `EnumWindows` 找到的**顶层窗口**，但真正收鼠标的可能是**子窗口**
     （cnc-ddraw 可能建子窗口渲染）。

本轮：
  S1 枚举该进程**全部窗口（含子窗口、含不可见）**，打印类名/尺寸/可见/是否含 "DDraw"/"GDI" 等线索
  S2 对每个候选窗口，用**按钮栏区域**这一可靠判据，测四种投递：
       A  SetCursorPos + SendInput（屏幕坐标，落在该窗口内时）
       B  PostMessage(hwnd, WM_MOUSEMOVE/WM_LBUTTONDOWN/UP, 客户区坐标)
       C  SendMessage(hwnd, ...) —— 同步投递，绕过消息队列
       D  PostMessage 到**每个子窗口**（逐层试）
  S3 报告哪个 (窗口, 方式) 组合真正改变了按钮栏
"""
import ctypes
import ctypes.wintypes as wt
import sys
import time
from pathlib import Path

PID = int(sys.argv[1]) if len(sys.argv) > 1 else 0
OUT = Path(r"D:\Project\ra2-campaign-forge\lead\re_d13_ruling_20261112")

u = ctypes.WinDLL("user32", use_last_error=True)
g = ctypes.WinDLL("gdi32", use_last_error=True)


class BMI(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG),
                ("biPlanes", wt.WORD), ("biBitCount", wt.WORD),
                ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG),
                ("biClrUsed", wt.DWORD), ("biClrImportant", wt.DWORD)]


class MI(ctypes.Structure):
    _fields_ = [("dx", wt.LONG), ("dy", wt.LONG), ("mouseData", wt.DWORD),
                ("dwFlags", wt.DWORD), ("time", wt.DWORD), ("dwExtraInfo", ctypes.c_void_p)]


class IN(ctypes.Structure):
    _fields_ = [("type", wt.DWORD), ("mi", MI)]


u.GetWindowDC.restype = ctypes.c_void_p
u.GetWindowDC.argtypes = [wt.HWND]
u.GetDC.restype = ctypes.c_void_p
u.GetDC.argtypes = [wt.HWND]
u.ReleaseDC.restype = ctypes.c_int
u.ReleaseDC.argtypes = [wt.HWND, ctypes.c_void_p]
u.GetWindowRect.restype = wt.BOOL
u.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u.GetClientRect.restype = wt.BOOL
u.GetClientRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u.GetWindowThreadProcessId.restype = wt.DWORD
u.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u.GetWindowTextLengthW.restype = ctypes.c_int
u.GetWindowTextLengthW.argtypes = [wt.HWND]
u.GetWindowTextW.restype = ctypes.c_int
u.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
u.GetClassNameW.restype = ctypes.c_int
u.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
u.IsWindowVisible.restype = wt.BOOL
u.IsWindowVisible.argtypes = [wt.HWND]
u.SetCursorPos.restype = wt.BOOL
u.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u.SendInput.restype = wt.UINT
u.SendInput.argtypes = [wt.UINT, ctypes.c_void_p, ctypes.c_int]
u.PostMessageW.restype = wt.BOOL
u.PostMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
u.SendMessageW.restype = ctypes.c_void_p
u.SendMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
u.SetForegroundWindow.restype = wt.BOOL
u.SetForegroundWindow.argtypes = [wt.HWND]
u.ClientToScreen.restype = wt.BOOL
u.ClientToScreen.argtypes = [wt.HWND, ctypes.POINTER(wt.POINT)]
u.EnumChildWindows.restype = wt.BOOL
u.EnumChildWindows.argtypes = [wt.HWND, ctypes.c_void_p, wt.LPARAM]
u.EnumWindows.restype = wt.BOOL
u.EnumWindows.argtypes = [ctypes.c_void_p, wt.LPARAM]

g.CreateCompatibleDC.restype = ctypes.c_void_p
g.CreateCompatibleDC.argtypes = [ctypes.c_void_p]
g.CreateCompatibleBitmap.restype = ctypes.c_void_p
g.CreateCompatibleBitmap.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
g.SelectObject.restype = ctypes.c_void_p
g.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
g.BitBlt.restype = wt.BOOL
g.BitBlt.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                     ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, wt.DWORD]
g.GetDIBits.restype = ctypes.c_int
g.GetDIBits.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wt.UINT, wt.UINT,
                        ctypes.c_void_p, ctypes.c_void_p, wt.UINT]
g.DeleteObject.restype = wt.BOOL
g.DeleteObject.argtypes = [ctypes.c_void_p]
g.DeleteDC.restype = wt.BOOL
g.DeleteDC.argtypes = [ctypes.c_void_p]

WNDENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
BUTTON_REGION = (650, 195, 141, 230)      # 渲染面内 800x600 的按钮栏


def wtext(h):
    n = u.GetWindowTextLengthW(h)
    b = ctypes.create_unicode_buffer(max(n + 1, 2))
    u.GetWindowTextW(h, b, n + 1)
    return b.value


def wclass(h):
    b = ctypes.create_unicode_buffer(256)
    u.GetClassNameW(h, b, 256)
    return b.value


def enum_process_windows(pid):
    """枚举该 pid 的全部窗口（顶层 + 递归子窗口）。"""
    tops = []

    def cb(h, l):
        q = wt.DWORD(0)
        u.GetWindowThreadProcessId(h, ctypes.byref(q))
        if q.value == pid:
            tops.append(h)
        return True

    u.EnumWindows(WNDENUMPROC(cb), 0)
    allw = []

    def walk(h, depth=0):
        allw.append((h, depth))
        kids = []

        def ccb(k, l):
            kids.append(k)
            return True

        u.EnumChildWindows(h, WNDENUMPROC(ccb), 0)
        for k in kids:
            walk(k, depth + 1)

    for t in tops:
        walk(t)
    return allw


def shot(hwnd):
    r = wt.RECT()
    if not u.GetWindowRect(hwnd, ctypes.byref(r)):
        return None
    w, h = r.right - r.left, r.bottom - r.top
    if w <= 0 or h <= 0:
        return None
    src = u.GetWindowDC(hwnd)
    if not src:
        return None
    m = g.CreateCompatibleDC(src)
    bmp = g.CreateCompatibleBitmap(src, w, h)
    g.SelectObject(m, bmp)
    g.BitBlt(m, 0, 0, w, h, src, 0, 0, 0x00CC0020)
    bi = BMI()
    bi.biSize = ctypes.sizeof(BMI)
    bi.biWidth = w
    bi.biHeight = -h
    bi.biPlanes = 1
    bi.biBitCount = 32
    stride = w * 4
    buf = (ctypes.c_char * (stride * h))()
    g.GetDIBits(m, bmp, 0, h, buf, ctypes.byref(bi), 0)
    g.DeleteObject(bmp)
    g.DeleteDC(m)
    u.ReleaseDC(hwnd, src)
    return (w, h, stride, bytes(buf))


def region_vals(w, h, stride, raw, region):
    x0, y0, rw, rh = region
    out = []
    for yy in range(y0, min(y0 + rh, h)):
        base = yy * stride
        for xx in range(x0, min(x0 + rw, w)):
            o = base + xx * 4
            out.append(raw[o] + raw[o + 1] + raw[o + 2])
    return out


def n_diff(a, b, thresh=24):
    if len(a) != len(b):
        return -1
    return sum(1 for x, y in zip(a, b) if abs(x - y) > thresh)


def mouse_input(down, x=0, y=0, absolute=False, move_only=False):
    i = IN()
    i.type = 0
    i.mi.dx, i.mi.dy = 0, 0
    flags = 0
    if absolute:
        sw, sh = u.GetSystemMetrics(0), u.GetSystemMetrics(1)
        i.mi.dx = int(x * 65535 / max(1, sw - 1))
        i.mi.dy = int(y * 65535 / max(1, sh - 1))
        flags |= 0x8000 | 0x4000
    if move_only:
        flags |= 0x0001
    elif down:
        flags |= 0x0002
    else:
        flags |= 0x0004
    i.mi.dwFlags = flags
    u.SendInput(1, ctypes.byref(i), ctypes.sizeof(IN))


def main():
    if not PID:
        print("用法: python _probe_window_input.py <pid>")
        return 2
    print("=" * 78)
    print("S1 · 枚举进程 %d 的全部窗口" % PID)
    print("=" * 78)
    ws = enum_process_windows(PID)
    print("共 %d 个窗口（含子窗口）\n" % len(ws))
    for h, d in ws:
        r = wt.RECT()
        u.GetWindowRect(h, ctypes.byref(r))
        cr = wt.RECT()
        u.GetClientRect(h, ctypes.byref(cr))
        print("  hwnd=%-10d depth=%d cls=%-26r title=%-20r rect=(%d,%d,%dx%d) client=%dx%d vis=%s"
              % (h, d, wclass(h), wtext(h)[:20],
                 r.left, r.top, r.right - r.left, r.bottom - r.top,
                 cr.right, cr.bottom, bool(u.IsWindowVisible(h))))

    # 找主窗口（有 Yuri 标题的）
    main_hwnd = None
    for h, d in ws:
        if "Yuri" in wtext(h):
            main_hwnd = h
            break
    if main_hwnd is None:
        print("\n!! 找不到主窗口")
        return 1

    print("\n" + "=" * 78)
    print("S2 · 逐个候选窗口 × 四种投递，用**按钮栏区域**判据")
    print("=" * 78)
    u.SetForegroundWindow(main_hwnd)
    time.sleep(0.6)

    base_shot = shot(main_hwnd)
    if not base_shot:
        print("!! 无法截图")
        return 1
    bw, bh, bs, braw = base_shot
    base = region_vals(bw, bh, bs, braw, BUTTON_REGION)
    print("基线按钮栏像素数 = %d（窗口 %dx%d）" % (len(base), bw, bh))

    # 候选窗口：主窗口 + 所有可见子窗口 + 所有 depth<=2
    cands = [(h, d) for h, d in ws if d <= 2]
    results = []

    for h, d in cands:
        r = wt.RECT()
        u.GetWindowRect(h, ctypes.byref(r))
        w, hh = r.right - r.left, r.bottom - r.top
        if w <= 0 or hh <= 0:
            continue
        pt = wt.POINT(0, 0)
        u.ClientToScreen(h, ctypes.byref(pt))
        row = {"hwnd": h, "depth": d, "cls": wclass(h), "rect": (r.left, r.top, w, hh)}
        # 计算按钮栏中心在该窗口客户区的坐标（按 800x600 → 实际尺寸映射）
        lx, ly = 700, 222
        cx = int(lx * w / 800.0)
        cy = int(ly * hh / 600.0)
        sx, sy = pt.x + cx, pt.y + cy

        tests = {}
        for tag in ("A_sendinput", "B_post_msg", "C_send_msg", "D_post_child"):
            u.SetForegroundWindow(main_hwnd)
            time.sleep(0.25)
            try:
                if tag == "A_sendinput":
                    u.SetCursorPos(int(sx), int(sy))
                    time.sleep(0.1)
                    mouse_input(True)
                    time.sleep(0.12)
                    mouse_input(False)
                elif tag == "B_post_msg":
                    lp = (int(cy) << 16) | (int(cx) & 0xFFFF)
                    u.PostMessageW(h, 0x0200, 0, lp)          # WM_MOUSEMOVE
                    time.sleep(0.06)
                    u.PostMessageW(h, 0x0201, 0x0001, lp)     # WM_LBUTTONDOWN
                    time.sleep(0.1)
                    u.PostMessageW(h, 0x0202, 0, lp)          # WM_LBUTTONUP
                elif tag == "C_send_msg":
                    lp = (int(cy) << 16) | (int(cx) & 0xFFFF)
                    u.SendMessageW(h, 0x0200, 0, lp)
                    time.sleep(0.06)
                    u.SendMessageW(h, 0x0201, 0x0001, lp)
                    time.sleep(0.1)
                    u.SendMessageW(h, 0x0202, 0, lp)
                elif tag == "D_post_child":
                    kids = []

                    def ccb(k, l):
                        kids.append(k)
                        return True

                    u.EnumChildWindows(h, WNDENUMPROC(ccb), 0)
                    for k in kids:
                        lp = (int(cy) << 16) | (int(cx) & 0xFFFF)
                        u.PostMessageW(k, 0x0200, 0, lp)
                        u.PostMessageW(k, 0x0201, 0x0001, lp)
                        time.sleep(0.05)
                        u.PostMessageW(k, 0x0202, 0, lp)
            except Exception as e:                          # noqa: BLE001
                tests[tag] = "EXC:%s" % type(e).__name__
                continue
            time.sleep(1.4)
            s2 = shot(main_hwnd)
            if not s2:
                tests[tag] = "NOSHOT"
                continue
            cur = region_vals(s2[0], s2[1], s2[2], s2[3], BUTTON_REGION)
            tests[tag] = n_diff(base, cur)
        row["tests"] = tests
        results.append(row)
        print("\n  hwnd=%-10d depth=%d cls=%r rect=%s"
              % (h, d, row["cls"], row["rect"]))
        for tag, v in tests.items():
            print("      %-14s 按钮栏差异 = %s" % (tag, v))

    # S3 汇总
    print("\n" + "=" * 78)
    print("S3 · 汇总：哪些组合真正改变了按钮栏（差异 > 200 视为有效）")
    print("=" * 78)
    hits = []
    for row in results:
        for tag, v in row["tests"].items():
            if isinstance(v, int) and v > 200:
                hits.append((row["hwnd"], row["cls"], tag, v))
    if hits:
        for h, cls, tag, v in hits:
            print("  ★ 有效: hwnd=%d cls=%r 方式=%s 差异=%d" % (h, cls, tag, v))
    else:
        print("  无任何组合生效（差异均 <= 200）")
        print("  ⇒ 确认：合成输入在本配置下整体不被消费")
    return 0


if __name__ == "__main__":
    sys.exit(main())
