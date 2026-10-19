"""重载基准：启动原版游戏 → 进遭遇战 → 采样，产出「单位数 vs 忙时」数据。

流程：
1. 把游戏切成窗口化（不抢屏、不重建窗口）
2. 配置 [Skirmish]：1 玩家 + 1 冷酷 AI，Credits 拉高
3. 启动 gamemd.exe，用截图 + 鼠标键盘走到遭遇战并开局
4. 对每档单位数的地图跑 `ra2re perf`，汇总成 curve

只读游戏文件做配置备份/还原；不碰 expandmd98.mix。
"""

from __future__ import annotations

import ctypes
import json
import os
import re
import subprocess
import sys
import time
from ctypes import wintypes
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GAME_DIR = PROJECT_ROOT / "ra2youli"
OUT_DIR = PROJECT_ROOT / "out" / "loadbench"
SHOTS = OUT_DIR / "shots"

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
user32.PrintWindow.restype = wintypes.BOOL
user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.BitBlt.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                         ctypes.c_int, wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.DWORD]
gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, ctypes.c_uint,
                            ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteDC.argtypes = [wintypes.HDC]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.QueryFullProcessImageNameW.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
user32.EnumWindows.argtypes = [ctypes.c_void_p, wintypes.LPARAM]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
user32.mouse_event.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
                               wintypes.DWORD, ctypes.c_void_p]
user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]

# --- Win32 小工具 -----------------------------------------------------------

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_MOVE = 0x0001

VK_ESCAPE = 0x1B
VK_RETURN = 0x0D
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("union", _INPUTUNION)]


def _send_key(vk: int, up: bool = False):
    inp = INPUT(type=INPUT_KEYBOARD)
    inp.union.ki = KEYBDINPUT(vk, 0, KEYEVENTF_KEYUP if up else 0, 0, None)
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def press_key(vk: int, hold: float = 0.03):
    _send_key(vk, False)
    time.sleep(hold)
    _send_key(vk, True)
    time.sleep(0.05)


def click(x: int, y: int, *, absolute: bool = True):
    """物理屏幕坐标点击。SetCursorPos + mouse_event，避开 DPI 下 ABSOLUTE 归一化误差。"""
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.08)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, None)
    time.sleep(0.04)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, None)
    time.sleep(0.12)


def find_gamemd_hwnd() -> int | None:
    """枚举顶层窗口，找 gamemd.exe 的可见主窗口。"""
    pid_buf = ctypes.c_ulong()
    result = {"hwnd": None}

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def enum_proc(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_buf))
        if not pid_buf.value:
            return True
        h = kernel32.OpenProcess(0x1000, False, pid_buf.value)  # PROCESS_QUERY_LIMITED
        if not h:
            return True
        try:
            name = ctypes.create_unicode_buffer(260)
            n = ctypes.c_ulong(260)
            # QueryFullProcessImageNameW
            if kernel32.QueryFullProcessImageNameW(h, 0, name, ctypes.byref(n)):
                base = os.path.basename(name.value).lower()
                if base == "gamemd.exe":
                    # 跳过 0 尺寸工具窗口
                    rect = ctypes.wintypes.RECT()
                    user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    if rect.right - rect.left > 100 and rect.bottom - rect.top > 100:
                        result["hwnd"] = hwnd
                        return False
        finally:
            kernel32.CloseHandle(h)
        return True

    user32.EnumWindows(enum_proc, 0)
    return result["hwnd"]


PW_RENDERFULLCONTENT = 0x00000002


dwmapi = ctypes.WinDLL("dwmapi", use_last_error=True)


def window_bbox(hwnd: int) -> tuple[int, int, int, int] | None:
    """优先 DWM 可见边界；GetWindowRect 对 cnc-ddraw 窗口会偏移。"""
    rect = wintypes.RECT()
    # DWMWA_EXTENDED_FRAME_BOUNDS = 9
    hr = dwmapi.DwmGetWindowAttribute(
        wintypes.HWND(hwnd), 9, ctypes.byref(rect), ctypes.sizeof(rect))
    if hr == 0 and rect.right > rect.left and rect.bottom > rect.top:
        return rect.left, rect.top, rect.right, rect.bottom
    if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return rect.left, rect.top, rect.right, rect.bottom
    return None


def grab_window_png(path: Path, hwnd: int) -> "object":
    """抓「屏幕上实际显示的」窗口区域。

    DirectDraw 游戏用 PrintWindow 抓不到内容，必须从**屏幕 DC** 按窗口矩形 BitBlt。
    调用前请把游戏窗口置于前台且未被遮挡。
    """
    from PIL import Image
    SHOTS.mkdir(parents=True, exist_ok=True)
    bbox = window_bbox(hwnd)
    if not bbox:
        raise RuntimeError("GetWindowRect failed")
    left, top, right, bottom = bbox
    w = max(right - left, 8)
    h = max(bottom - top, 8)
    screen = user32.GetDC(0)
    memdc = gdi32.CreateCompatibleDC(screen)
    hbmp = gdi32.CreateCompatibleBitmap(screen, w, h)
    gdi32.SelectObject(memdc, hbmp)
    # SRCCOPY = 0x00CC0020
    gdi32.BitBlt(memdc, 0, 0, w, h, screen, left, top, 0x00CC0020)

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [("biSize", ctypes.c_ulong), ("biWidth", ctypes.c_long),
                    ("biHeight", ctypes.c_long), ("biPlanes", ctypes.c_ushort),
                    ("biBitCount", ctypes.c_ushort), ("biCompression", ctypes.c_ulong),
                    ("biSizeImage", ctypes.c_ulong), ("biXPelsPerMeter", ctypes.c_long),
                    ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", ctypes.c_ulong),
                    ("biClrImportant", ctypes.c_ulong)]

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(memdc, hbmp, 0, h, buf, ctypes.byref(bmi), 0)
    img = Image.frombuffer("RGBA", (w, h), buf.raw, "raw", "BGRA", 0, 1).convert("RGB")
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(memdc)
    user32.ReleaseDC(0, screen)
    img.save(path)
    return img


def grab_png(path: Path, hwnd: int | None = None):
    if hwnd:
        return grab_window_png(path, hwnd)
    from PIL import ImageGrab
    SHOTS.mkdir(parents=True, exist_ok=True)
    img = ImageGrab.grab()
    img.save(path)
    return img


def click_window(hwnd: int, lx: int, ly: int, *, logic_w: int = 800, logic_h: int = 600):
    """按游戏 800x600 逻辑坐标点击；用 DWM 边界换算屏幕坐标。"""
    raise_game(hwnd)
    time.sleep(0.15)
    bbox = window_bbox(hwnd)
    if not bbox:
        raise RuntimeError("no window bbox")
    left, top, right, bottom = bbox
    cw = max(right - left, 1)
    ch = max(bottom - top, 1)
    sx = left + int(lx / logic_w * cw)
    sy = top + int(ly / logic_h * ch)
    click(sx, sy)


# --- 游戏配置 ---------------------------------------------------------------

@dataclass
class GameConfig:
    ddraw: str
    ra2md: str
    backups: dict = field(default_factory=dict)


def _read(p: Path) -> str:
    return p.read_text(encoding="gbk", errors="replace")


def _write(p: Path, text: str):
    p.write_text(text, encoding="gbk", errors="replace")


def apply_bench_config(game_dir: Path, *, unit_count: int = 10) -> GameConfig:
    """窗口化 + 遭遇战 1 人 + 1 冷酷 AI。返回备份用原文。"""
    ddraw = game_dir / "ddraw.ini"
    ra2md = game_dir / "RA2MD.INI"
    cfg = GameConfig(ddraw=_read(ddraw), ra2md=_read(ra2md))

    t = cfg.ddraw
    t2 = re.sub(r"(?m)^windowed\s*=\s*\w+", "windowed=true", t)
    if t2 == t and "windowed" not in t.lower():
        t2 += "\nwindowed=true\n"
    _write(ddraw, t2)

    t = cfg.ra2md
    # [Skirmish] 段整段替换关键项
    def set_skirmish_key(text: str, key: str, val: str) -> str:
        pat = re.compile(rf"(?m)^({re.escape(key)}\s*=\s*).*$")
        if pat.search(text):
            return pat.sub(rf"\g<1>{val}", text, count=1)
        return text

    # 只改 [Skirmish] 段里的键：先截出该段
    m = re.search(r"(?ms)^(\[Skirmish\].*?)(?=^\[)", t)
    if not m:
        t += "\n[Skirmish]\nGameMode=1\n"
        m = re.search(r"(?ms)^(\[Skirmish\].*?)(?=^\[)", t)
    seg = m.group(1)
    for k, v in [
        ("UnitCount", str(unit_count)),
        ("Credits", "10000"),
        ("ShortGame", "no"),
        ("CratesAppear", "no"),
        ("SuperWeaponsAllowed", "yes"),
        ("GameSpeed", "2"),
        # Slot: 8=Russians (P1), 0=Americans (AI)
        ("Slot01", "8,-2,-2"),
        ("Slot02", "0,-2,-2"),
    ]:
        if re.search(rf"(?m)^{k}=", seg):
            seg = re.sub(rf"(?m)^({k}=).*$", rf"\g<1>{v}", seg, count=1)
        else:
            seg = seg.rstrip() + f"\n{k}={v}\n"
    t = t[: m.start(1)] + seg + t[m.end(1) :]
    _write(ra2md, t)
    return cfg


def restore_config(game_dir: Path, cfg: GameConfig):
    _write(game_dir / "ddraw.ini", cfg.ddraw)
    _write(game_dir / "RA2MD.INI", cfg.ra2md)


# --- 启动与导航 -------------------------------------------------------------

def launch_game(game_dir: Path) -> subprocess.Popen:
    loader = game_dir / "ra2loader.exe"
    exe = loader if loader.is_file() else (game_dir / "gamemd.exe")
    # 以前台子进程启动，便于拿到退出码
    return subprocess.Popen(
        [str(exe)], cwd=str(game_dir),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


SW_MINIMIZE = 6
SW_RESTORE = 9


def minimize_other_windows(keep_hwnd: int):
    """把除游戏外的可见顶层窗口最小化，保证 BitBlt 抓到的是游戏画面。"""
    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def enum_proc(hwnd, _lparam):
        if hwnd == keep_hwnd or not user32.IsWindowVisible(hwnd):
            return True
        # 跳过任务栏/桌面
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, 256)
        if cls.value in ("Shell_TrayWnd", "Progman", "WorkerW", "Windows.UI.Core.CoreWindow"):
            return True
        user32.ShowWindow(hwnd, SW_MINIMIZE)
        return True

    user32.EnumWindows(enum_proc, 0)


def raise_game(hwnd: int):
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)
    user32.BringWindowToTop(hwnd)
    time.sleep(0.25)


def wait_window(timeout: float = 20.0) -> int | None:
    t_end = time.time() + timeout
    while time.time() < t_end:
        hwnd = find_gamemd_hwnd()
        if hwnd:
            raise_game(hwnd)
            return hwnd
        time.sleep(0.4)
    return None


def try_enter_skirmish(hwnd: int, tag: str) -> bool:
    """尽力用截图+点击进遭遇战。失败返回 False，留给人工。"""
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.3)
    # 跳过开场动画
    press_key(VK_ESCAPE)
    time.sleep(0.6)
    press_key(VK_ESCAPE)
    time.sleep(0.8)
    grab_png(SHOTS / f"{tag}_menu.png", hwnd=hwnd)

    # 主菜单：单人游戏（800x600 逻辑坐标，中列）
    click_window(hwnd, 400, 220)
    time.sleep(1.0)
    grab_png(SHOTS / f"{tag}_after_sp.png", hwnd=hwnd)

    # 单人子菜单：遭遇战
    click_window(hwnd, 400, 304)
    time.sleep(1.4)
    grab_png(SHOTS / f"{tag}_skirmish.png", hwnd=hwnd)
    return True


# --- 主流程 -----------------------------------------------------------------

def run_one(units: int, *, seconds: float = 45.0, skip_nav: bool = False) -> dict | None:
    """对一档单位数：确保地图在位 → 配置 → 开局 → 采样。"""
    from . import perf
    from . import loadbench

    game_dir = GAME_DIR
    map_name = f"0LoadBench_U{units:04d}"
    map_path = game_dir / f"[2]{map_name}.yrm"
    if not map_path.is_file():
        print(f"  生成缺失的地图 {map_path.name}")
        loadbench.write_loadbench(units, game_dir, size=100)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    symbols = OUT_DIR / "symbols.json"
    if not symbols.is_file():
        # 复用 reverse 产物
        src = PROJECT_ROOT / "out" / "reverse" / "symbols.json"
        blit_src = PROJECT_ROOT / "out" / "reverse" / "m1_blit_targets.txt"
        if src.is_file():
            symbols.write_bytes(src.read_bytes())
        blit = OUT_DIR / "m1_blit_targets.txt"
        if blit_src.is_file() and not blit.is_file():
            blit.write_bytes(blit_src.read_bytes())
    blit = OUT_DIR / "m1_blit_targets.txt"

    print(f"== 载荷 {units} 单位：配置并启动游戏")
    cfg = apply_bench_config(game_dir, unit_count=10)
    try:
        # 若已有游戏在跑，先不强制杀（可能是用户自己的）
        if perf.find_pid("gamemd.exe"):
            print("  gamemd.exe 已在运行，直接采样（请确保已进入 LoadBench 地图）")
            time.sleep(2)
        else:
            proc = launch_game(game_dir)
            hwnd = wait_window(25)
            if not hwnd:
                print("  找不到游戏窗口", file=sys.stderr)
                return None
            if not skip_nav:
                try_enter_skirmish(hwnd, f"u{units}")
                print("  已尝试导航到遭遇战；若未开局，请手动进入 "
                      f"{map_name} 并开始，然后在 20 秒内不要动鼠标")
                # 给人工兜底时间
                time.sleep(20)

        # 采样
        print(f"  采样 {seconds:.0f}s …")
        res = perf.profile("gamemd.exe", seconds=seconds, hz=500.0,
                           symbols_json=symbols, blit_file=blit if blit.is_file() else None)
        payload = res.as_dict()
        payload["units"] = units
        payload["map"] = map_name
        outp = OUT_DIR / f"perf_U{units:04d}.json"
        outp.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                        encoding="utf-8")
        busy = 1.0 - (res.by_class.get("idle", 0) + res.by_module.get("idle", 0)) / max(res.samples, 1)
        # 用模块占比粗算
        gm = res.by_module.get("gamemd.exe", 0) + res.by_module.get("Gamemd.exe", 0)
        print(f"  样本 {res.samples}  gamemd 模块 {100.0*gm/max(res.samples,1):.1f}%  → {outp.name}")
        return payload
    finally:
        restore_config(game_dir, cfg)


def summarize() -> Path:
    rows = []
    for p in sorted(OUT_DIR.glob("perf_U*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        total = max(data.get("samples", 1), 1)
        by_mod = data.get("by_module") or {}
        by_cls = data.get("by_class") or {}
        gm = sum(v for k, v in by_mod.items() if k.lower().startswith("gamemd"))
        blit = sum(v for k, v in by_cls.items() if k == "blit")
        idle = by_cls.get("idle", 0) + by_cls.get("text_unknown", 0) * 0  # idle 若无则为 0
        # 空闲样本一般落在 win32u / 其他模块
        idle_mod = sum(v for k, v in by_mod.items()
                       if any(s in k.lower() for s in ("win32u", "user32", "ntdll", "idle")))
        rows.append({
            "units": data.get("units"),
            "samples": data.get("samples"),
            "gamemd_pct": round(100.0 * gm / total, 2),
            "blit_busy_pct": round(100.0 * blit / max(gm, 1), 2),
            "top": sorted((data.get("top_symbols") or {}).items(), key=lambda x: -x[1])[:5],
        })
    rows.sort(key=lambda r: r.get("units") or 0)
    md = [
        "# 重载基准：单位数 vs 时间分布", "",
        "| 单位数 | 样本 | gamemd 占比 | blit/ gamemd | Top 热点 |",
        "|---:|---:|---:|---:|---|",
    ]
    for r in rows:
        tops = ", ".join(f"{k} {v}" for k, v in r["top"][:3])
        md.append(f"| {r['units']} | {r['samples']} | {r['gamemd_pct']}% | "
                  f"{r['blit_busy_pct']}% | {tops} |")
    md += ["", "## 说明", "",
           "- `gamemd 占比` = 落在 gamemd.exe 模块内的样本比例（越高越忙）",
           "- `blit / gamemd` = blit 族在 gamemd 样本中的占比（L1 收益上限的代理指标）",
           "- 采样工具：`python -m ra2re perf`（零侵入读 EIP）", ""]
    out = OUT_DIR / "loadbench-report.md"
    out.write_text("\n".join(md), encoding="utf-8")
    return out


def wait_until_busy(seconds: float = 180.0, *, hz: float = 50.0) -> bool:
    """短采样探测是否已进入对局（blit 样本出现即认为在游戏里）。"""
    from . import perf
    t_end = time.time() + seconds
    while time.time() < t_end:
        try:
            res = perf.profile("gamemd.exe", seconds=2.0, hz=hz,
                               symbols_json=PROJECT_ROOT / "out" / "loadbench" / "symbols.json",
                               blit_file=PROJECT_ROOT / "out" / "loadbench" / "m1_blit_targets.txt")
        except RuntimeError:
            time.sleep(1)
            continue
        blit = res.by_class.get("blit", 0)
        gm = sum(v for k, v in res.by_module.items() if k.lower().startswith("gamemd"))
        if blit >= 5 or gm / max(res.samples, 1) > 0.15:
            return True
        time.sleep(0.5)
    return False


def run_manual_suite(units: list[int], *, seconds: float = 45.0) -> int:
    """人工开局 + 自动采样：每档等你点进对应地图后自动测。"""
    from . import loadbench, perf

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    symbols = OUT_DIR / "symbols.json"
    if not symbols.is_file():
        src = PROJECT_ROOT / "out" / "reverse" / "symbols.json"
        if src.is_file():
            symbols.write_bytes(src.read_bytes())
    blit = OUT_DIR / "m1_blit_targets.txt"

    for u in units:
        map_name = f"0LoadBench_U{u:04d}"
        map_path = GAME_DIR / f"[2]{map_name}.yrm"
        if not map_path.is_file():
            loadbench.write_loadbench(u, GAME_DIR, size=100)

        print()
        print("=" * 60)
        print(f"  档位 {u} 单位　地图：{map_name}")
        print("  请在游戏里：单人游戏 → 遭遇战 → 选中该图 → 开始")
        print("  进入战场后 2 分钟内会自动采样，期间请勿退出。")
        print("=" * 60)

        if not perf.find_pid("gamemd.exe"):
            cfg = apply_bench_config(GAME_DIR, unit_count=10)
            launch_game(GAME_DIR)
            wait_window(25)
            # 配置在退出时统一还原
            print("  游戏已启动，请手动进图。")
            time.sleep(3)
            _PENDING_CFG.append(cfg)
        else:
            print("  检测到游戏已在运行。")

        print("  等待进入对局…")
        if not wait_until_busy(180):
            print("  ⚠ 180s 内未检测到对局负载，跳过本档", file=sys.stderr)
            continue

        print(f"  采样 {seconds:.0f}s …")
        res = perf.profile("gamemd.exe", seconds=seconds, hz=500.0,
                           symbols_json=symbols,
                           blit_file=blit if blit.is_file() else None)
        payload = res.as_dict()
        payload["units"] = u
        payload["map"] = map_name
        (OUT_DIR / f"perf_U{u:04d}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        total = max(res.samples, 1)
        gm = sum(v for k, v in res.by_module.items() if k.lower().startswith("gamemd"))
        bl = res.by_class.get("blit", 0)
        print(f"  ✅ {u} 单位：gamemd {100*gm/total:.1f}%  blit/gamemd {100*bl/max(gm,1):.1f}%")

        # 下一档前请用户退到大厅换图
        if u != units[-1]:
            print("  请退出本局，换下一张 LoadBench 地图…")
            time.sleep(8)

    for cfg in _PENDING_CFG:
        restore_config(GAME_DIR, cfg)
    _PENDING_CFG.clear()
    out = summarize()
    print("\n报告：", out)
    return 0


_PENDING_CFG: list = []


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(prog="ra2re loadrun")
    p.add_argument("units", nargs="*", type=int, default=[50, 200, 400],
                   help="要测的单位数档位")
    p.add_argument("--seconds", type=float, default=45.0)
    p.add_argument("--skip-nav", action="store_true",
                   help="不自动点菜单（游戏已在目标对局中时用）")
    p.add_argument("--manual", action="store_true",
                   help="人工开局，脚本只负责采样（推荐，绕过 DirectInput）")
    p.add_argument("--summarize-only", action="store_true")
    args = p.parse_args(argv)

    if args.summarize_only:
        out = summarize()
        print("报告：", out)
        return 0

    if args.manual:
        return run_manual_suite(args.units or [50, 200, 400], seconds=args.seconds)

    results = []
    for u in args.units:
        print(f"\n---- LoadBench {u} ----")
        r = run_one(u, seconds=args.seconds, skip_nav=args.skip_nav)
        if r:
            results.append(r)
        os.system("taskkill /IM gamemd.exe /F >nul 2>&1")
        time.sleep(1.5)

    out = summarize()
    print("\n报告：", out)
    return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())
