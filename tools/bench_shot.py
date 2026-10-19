#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bench_shot.py — 真机全屏/窗口截图工具（per-monitor-v2 DPI 感知，真实物理像素）。

与 bench_replay.grab 的区别：本工具在进程启动最早阶段设置 PER_MONITOR_AWARE_V2，
GetWindowRect / BitBlt 全部使用真实物理像素，不产生 DPI 虚拟化错位。

用法：
  python tools/bench_shot.py --full --out a.png            # 全屏
  python tools/bench_shot.py --window --out b.png          # 游戏窗口（真实 bbox）
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import sys
import time
from ctypes import wintypes
from pathlib import Path

# —— 必须在任何 GDI/USER 调用之前设置 DPI 感知 ——
try:
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))  # PMv2
except Exception:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
dwmapi = ctypes.WinDLL("dwmapi", use_last_error=True)


def find_game_hwnd() -> int | None:
    result = {"hwnd": None, "any": []}
    pid_buf = ctypes.c_ulong()

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def proc(hwnd, _):
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_buf))
        if pid_buf.value:
            import subprocess
            result.setdefault("pids", set())
        return True

    # 用 tasklist 找 pid 更省事
    import subprocess
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq gamemd.exe", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True, errors="replace").stdout
    pids = []
    for line in out.splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) >= 2 and parts[0].lower().startswith("gamemd"):
            try:
                pids.append(int(parts[1]))
            except ValueError:
                pass
    if not pids:
        return None
    target = set(pids)

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def scan(hwnd, _):
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_buf))
        if pid_buf.value in target:
            r = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(r))
            w, h = r.right - r.left, r.bottom - r.top
            if w > 100 and h > 100:
                if result["hwnd"] is None and user32.IsWindowVisible(hwnd):
                    result["hwnd"] = hwnd
                result["any"].append((hwnd, w, h, bool(user32.IsWindowVisible(hwnd))))
        return True

    user32.EnumWindows(scan, 0)
    if result["hwnd"] is None and result["any"]:
        result["hwnd"] = result["any"][0][0]
    return result["hwnd"]


def capture(x: int, y: int, w: int, h: int, path: Path) -> dict:
    from PIL import Image
    path.parent.mkdir(parents=True, exist_ok=True)
    sdc = user32.GetDC(0)
    mdc = gdi32.CreateCompatibleDC(sdc)
    hbmp = gdi32.CreateCompatibleBitmap(sdc, w, h)
    gdi32.SelectObject(mdc, hbmp)
    gdi32.BitBlt(mdc, 0, 0, w, h, sdc, x, y, 0x00CC0020)

    class BMIH(ctypes.Structure):
        _fields_ = [("biSize", ctypes.c_ulong), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long),
                    ("biPlanes", ctypes.c_ushort), ("biBitCount", ctypes.c_ushort), ("biCompression", ctypes.c_ulong),
                    ("biSizeImage", ctypes.c_ulong), ("biXPPM", ctypes.c_long), ("biYPPM", ctypes.c_long),
                    ("biClrUsed", ctypes.c_ulong), ("biClrImportant", ctypes.c_ulong)]

    bmi = BMIH(ctypes.sizeof(BMIH), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mdc, hbmp, 0, h, buf, ctypes.byref(bmi), 0)
    img = Image.frombuffer("RGB", (w, h), buf.raw, "raw", "BGRX", 0, 1)
    img.save(path)
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(mdc)
    user32.ReleaseDC(0, sdc)

    raw = path.read_bytes()
    px = img.resize((80, 80))
    colors = len(set(px.getdata()))
    gray = list(px.convert("L").getdata())
    mean = sum(gray) / len(gray)
    var = sum((v - mean) ** 2 for v in gray) / len(gray)
    # md5 仅作同批次截图去重指纹（证据标准 v2 要求），非安全用途；sha256 供完整性核验
    return {"path": str(path.resolve()), "width": w, "height": h, "bytes": len(raw),
            "md5": hashlib.md5(raw).hexdigest(), "sha256": hashlib.sha256(raw).hexdigest(),
            "colors80": colors, "luma_var": round(var, 1)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="bench_shot")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--window", action="store_true")
    ap.add_argument("--out", required=True)
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args(argv)

    sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    out = Path(args.out)
    recs = []
    if args.full or not args.window:
        recs.append(capture(0, 0, sw, sh, out))
    if args.window:
        hwnd = find_game_hwnd()
        if not hwnd:
            print("[FAIL] 未找到 gamemd 窗口")
            return 1
        r = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(r))
        d = wintypes.RECT()
        hr = dwmapi.DwmGetWindowAttribute(ctypes.c_void_p(hwnd), 9, ctypes.byref(d), ctypes.sizeof(d))
        print(f"hwnd={hwnd} GetWindowRect=({r.left},{r.top},{r.right},{r.bottom}) "
              f"wh={r.right - r.left}x{r.bottom - r.top}")
        if hr == 0:
            print(f"  DWMWA_EXTENDED_FRAME_BOUNDS=({d.left},{d.top},{d.right},{d.bottom}) "
                  f"wh={d.right - d.left}x{d.bottom - d.top}")
        cr = wintypes.RECT()
        user32.GetClientRect(hwnd, ctypes.byref(cr))
        pt = wintypes.POINT(0, 0)
        user32.ClientToScreen(hwnd, ctypes.byref(pt))
        print(f"  GetClientRect={cr.right - cr.left}x{cr.bottom - cr.top} client_screen_origin=({pt.x},{pt.y})")
        rc = r
        recs.append(capture(rc.left, rc.top, rc.right - rc.left, rc.bottom - rc.top, out))

    for m in recs:
        print(f"{m['path']}  {m['width']}x{m['height']}  {m['bytes']}B  md5={m['md5'][:10]} "
              f"colors80={m['colors80']} luma_var={m['luma_var']}")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(recs, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
