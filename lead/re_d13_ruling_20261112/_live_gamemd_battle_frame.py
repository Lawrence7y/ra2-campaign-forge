# -*- coding: utf-8 -*-
"""E3 对战内帧号推进验证：复现母本的「主菜单 → 对战」导航，确认 G_FRAME 真的推进。

导航序列（**照抄母本 `_drive_c2_x_probe_v2.py:629-644`，未改动**）：
    sleep(35.0)                             # 等主菜单就绪
    对 (700,218) / (700,304) / (700,262) 依次：
        nav_focus(hwnd) → nav_click(hwnd, lx, ly) → sleep(12.0)
    然后 phase_sentinels ×2（间隔 3s），判 frame 差值 >= 8 ⇒ in_battle

点击方式（与母本 H7.click_logical 同口径）：
    逻辑 800×600 坐标 + 窗口原点平移 ⇒ SetCursorPos + SendInput（真实用户输入）
    **不改游戏内存、不注入、不发窗口消息。**

本脚本只做**只读帧号轮询**，不挂起线程、不做栈回溯。
"""
import ctypes
import ctypes.wintypes as wt
import subprocess
import sys
import time

GAME_DIR = r"D:\Project\ra2-campaign-forge\ra2youli"
GAME_EXE = GAME_DIR + r"\gamemd.exe"
G_FRAME = 0x00A8ED84
G_TICK = 0x00A8ED80
G_SINGLETON = 0x00887368
G_EXITSTATE = 0x00A8EDD8

NAV_CHAIN = ((700, 218), (700, 304), (700, 262))   # 母本 QC141:93
MENU_WAIT = 35.0
CLICK_WAIT = 12.0
IN_BATTLE_MIN_DELTA = 8

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.CloseHandle.argtypes = [wt.HANDLE]
k32.ReadProcessMemory.restype = wt.BOOL
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
user32.SetCursorPos.argtypes = [wt.INT, wt.INT]
user32.SetCursorPos.restype = wt.BOOL
user32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
user32.GetWindowRect.restype = wt.BOOL
user32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
user32.GetWindowTextLengthW.argtypes = [wt.HWND]
user32.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, wt.INT]
user32.SetForegroundWindow.argtypes = [wt.HWND]
user32.ShowWindow.argtypes = [wt.HWND, wt.INT]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wt.LONG), ("dy", wt.LONG), ("mouseData", wt.DWORD),
                ("dwFlags", wt.DWORD), ("time", wt.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wt.DWORD), ("mi", MOUSEINPUT)]


ENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)


def find_window(pid):
    found = []

    def cb(hwnd, lp):
        p = wt.DWORD(0)
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid:
            n = user32.GetWindowTextLengthW(hwnd)
            if n:
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                if buf.value and "Yuri" in buf.value:
                    found.append(hwnd)
        return True

    user32.EnumWindows(ENUMPROC(cb), 0)
    return found[0] if found else None


_SURFACE = {"origin": None, "size": None}


def detect_render_surface(hwnd):
    """自动检测渲染面（非黑区域包围盒）。

    背景：窗口可能被拉伸到 1707x960，但真正的 800x600 渲染面位于其中一块，
    其余为黑边。母本 click_logical_fullscreen 假设渲染面原点 = 窗口原点，
    在本机不成立 ⇒ 点击落到黑区，进不了对战。
    本函数用 BitBlt 截屏找非黑包围盒，得出真实 origin/size。
    """
    u, g = user32, gdi32
    rc = wt.RECT()
    u.GetWindowRect(hwnd, ctypes.byref(rc))
    w, h = rc.right - rc.left, rc.bottom - rc.top
    hdcS = u.GetDC(0)
    hdcM = g.CreateCompatibleDC(hdcS)
    bmp = g.CreateCompatibleBitmap(hdcS, w, h)
    g.SelectObject(hdcM, bmp)
    g.BitBlt(hdcM, 0, 0, w, h, hdcS, rc.left, rc.top, 0x00CC0020)
    class BMI(ctypes.Structure):
        _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG),
                    ("biPlanes", wt.WORD), ("biBitCount", wt.WORD),
                    ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                    ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG),
                    ("biClrUsed", wt.DWORD), ("biClrImportant", wt.DWORD)]
    bi = BMI()
    bi.biSize = ctypes.sizeof(BMI); bi.biWidth = w; bi.biHeight = -h
    bi.biPlanes = 1; bi.biBitCount = 32; bi.biCompression = 0
    stride = w * 4
    buf = (ctypes.c_char * (stride * h))()
    g.GetDIBits(hdcM, bmp, 0, h, buf, ctypes.byref(bi), 0)
    g.DeleteObject(bmp); g.DeleteDC(hdcM); u.ReleaseDC(0, hdcS)
    raw = bytes(buf)
    minx, miny, maxx, maxy = w, h, -1, -1
    step = 4                      # 粗采样，够找包围盒
    for yy in range(0, h, step):
        base = yy * stride
        for xx in range(0, w, step):
            o = base + xx * 4
            b, gg, r = raw[o], raw[o + 1], raw[o + 2]
            if b > 8 or gg > 8 or r > 8:
                if xx < minx: minx = xx
                if xx > maxx: maxx = xx
                if yy < miny: miny = yy
                if yy > maxy: maxy = yy
    if maxx < 0:
        return None
    _SURFACE["origin"] = (rc.left + minx, rc.top + miny)
    _SURFACE["size"] = (maxx - minx + step, maxy - miny + step)
    return _SURFACE


def click_logical(hwnd, lx, ly):
    """逻辑 800×600 坐标 → 屏坐标（按窗口原点平移），用 SetCursorPos+SendInput 点击。"""
    rc = wt.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rc)):
        return False
    # 若检测到渲染面，按 (800x600 -> surface) 映射；否则退回窗口原点直通
    if _SURFACE["origin"] and _SURFACE["size"]:
        ox, oy = _SURFACE["origin"]
        sw, sh = _SURFACE["size"]
        sx = int(ox + lx * sw / 800.0)
        sy = int(oy + ly * sh / 600.0)
    else:
        sx, sy = rc.left + lx, rc.top + ly
    user32.SetCursorPos(int(sx), int(sy))
    time.sleep(0.08)
    inp = INPUT()
    inp.type = 0                          # INPUT_MOUSE
    inp.mi.dx = 0
    inp.mi.dy = 0
    inp.mi.mouseData = 0
    inp.mi.dwFlags = 0x0002               # MOUSEEVENTF_LEFTDOWN
    inp.mi.time = 0
    inp.mi.dwExtraInfo = None
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
    time.sleep(0.06)
    inp.mi.dwFlags = 0x0004               # MOUSEEVENTF_LEFTUP
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
    return True


def reader(h):
    def rd(addr):
        b = (ctypes.c_char * 4)()
        n = ctypes.c_size_t(0)
        ok = k32.ReadProcessMemory(h, ctypes.c_void_p(addr), b, 4, ctypes.byref(n))
        return int.from_bytes(b.raw, "little") if ok and n.value == 4 else None
    return rd


def main():
    fails = []
    n = {"v": 0}

    def t(name, cond, ev=""):
        n["v"] += 1
        print("[%s] %-52s %s" % ("OK" if cond else "RED", name, ev))
        if not cond:
            fails.append(name)

    print("=" * 78)
    print("E3 对战内帧号推进验证（复现母本导航序列）")
    print("=" * 78)

    proc = subprocess.Popen([GAME_EXE], cwd=GAME_DIR,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("gamemd.exe pid = %d" % proc.pid)
    h = None
    try:
        time.sleep(6.0)
        h = k32.OpenProcess(0x0010 | 0x0400, False, proc.pid)
        t("OpenProcess 成功", bool(h), "h=%r" % h)
        if not h:
            return 1
        rd = reader(h)

        hwnd = find_window(proc.pid)
        t("找到游戏主窗口", hwnd is not None, "hwnd=%r" % hwnd)
        if not hwnd:
            return 1
        user32.ShowWindow(hwnd, 5)        # SW_SHOW
        user32.SetForegroundWindow(hwnd)

        surf = detect_render_surface(hwnd)
        if surf:
            print("渲染面: origin=%s size=%s（窗口 %s）"
                  % (surf["origin"], surf["size"],
                     (wt.RECT(), ) and ""))
        else:
            print("!! 未检测到渲染面")
        print("\n初始哨兵: tick=%s frame=%s singleton=%s"
              % (rd(G_TICK), rd(G_FRAME), rd(G_SINGLETON)))
        t("初始 G_FRAME 可读", rd(G_FRAME) is not None)

        print("\n-- 等主菜单 %gs --" % MENU_WAIT)
        time.sleep(MENU_WAIT)
        f_menu = rd(G_FRAME)
        print("菜单态 G_FRAME = %s" % f_menu)

        print("\n-- 导航点击（母本序列）--")
        for i, (lx, ly) in enumerate(NAV_CHAIN):
            user32.SetForegroundWindow(hwnd)
            ok = click_logical(hwnd, lx, ly)
            print("  点击 #%d (%d,%d) -> %s，等 %.0fs"
                  % (i + 1, lx, ly, "ok" if ok else "fail", CLICK_WAIT))
            time.sleep(CLICK_WAIT)

        print("\n-- 对战判定（母本口径：frame 两次差 >= %d）--" % IN_BATTLE_MIN_DELTA)
        f0 = rd(G_FRAME)
        time.sleep(3.0)
        f1 = rd(G_FRAME)
        print("  f0=%s f1=%s delta=%s" % (f0, f1, (f1 - f0) if (f0 is not None and f1 is not None) else "?"))
        in_battle = (f0 is not None and f1 is not None and (f1 - f0) >= IN_BATTLE_MIN_DELTA)
        t("进入对战（frame delta >= %d）" % IN_BATTLE_MIN_DELTA, in_battle,
          "delta=%s" % ((f1 - f0) if (f0 is not None and f1 is not None) else "?"))

        # 再连续轮询，确认持续推进
        print("\n-- 对战内连续轮询 10s --")
        vals = []
        for i in range(20):
            v = rd(G_FRAME)
            vals.append(v)
            if i % 5 == 0:
                print("    t=%.1fs frame=%s tick=%s" % (i * 0.5, v, rd(G_TICK)))
            time.sleep(0.5)
        good = [v for v in vals if v is not None]
        print("  可读 %d/%d, 不同值 %d, min=%s max=%s"
              % (len(good), len(vals), len(set(good)),
                 min(good) if good else "-", max(good) if good else "-"))
        advancing = len(set(good)) > 1
        t("G_FRAME 在对战内持续推进", advancing,
          "distinct=%d" % len(set(good)))
        if advancing:
            d = [good[i + 1] - good[i] for i in range(len(good) - 1)]
            nz = [x for x in d if x != 0]
            # 0.5s 采样间隔下的帧增量 ⇒ 推算 fps
            if nz:
                import statistics
                med = statistics.median(nz)
                print("  Δ 中位=%s 非零Δ=%d/%d  ⇒ 约 %.1f fps（0.5s 采样）"
                      % (med, len(nz), len(d), med / 0.5))
                t("帧率落在合理区间(10~120 fps)", 10 <= med / 0.5 <= 120,
                  "%.1f fps" % (med / 0.5))

        print("\n-- 安全 --")
        t("游戏仍存活（未被我搞死）", proc.poll() is None, "poll=%r" % proc.poll())
    finally:
        if h:
            k32.CloseHandle(h)
        try:
            proc.terminate(); proc.wait(timeout=10)
            print("\n已终止 gamemd.exe rc=%r" % proc.returncode)
        except Exception as e:                            # noqa: BLE001
            print("\n终止失败: %s" % e)

    print("\n" + "=" * 78)
    print("结果：%d 项检查，%d 项失败%s" % (n["v"], len(fails),
                                     "" if not fails else "：%s" % fails))
    print("=" * 78)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
