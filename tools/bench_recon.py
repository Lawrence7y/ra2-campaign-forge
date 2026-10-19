#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bench_recon.py — 真机侦察：启动游戏、报告窗口几何、抓图存证（只读）。

用途：校准分辨率与 UI 坐标（导航/建造按钮），不做任何 ini 写入。
用法：python tools/bench_recon.py --tag recon1 [--shots N] [--wait 25]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_replay as B  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="bench_recon")
    ap.add_argument("--tag", default="recon")
    ap.add_argument("--wait", type=float, default=25.0, help="启动后等待秒数（菜单就绪 ~20s）")
    ap.add_argument("--shots", type=int, default=1)
    ap.add_argument("--keep", action="store_true", help="保留游戏进程（便于下一步交互）")
    ap.add_argument("--no-nav", action="store_true", help="不执行任何按键/点击")
    args = ap.parse_args(argv)

    shots = B.SHOTS / "recon"
    shots.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%H%M%S")

    B.kill_game()
    pid = B.launch()
    proc = B.open_proc(pid)
    hwnd = None
    t_end = time.time() + 20
    while time.time() < t_end and not hwnd:
        hwnd = B.find_game_hwnd(pid)
        time.sleep(0.5)

    rec = {"pid": pid, "hwnd": hwnd, "ts": datetime.now().isoformat(timespec="seconds")}
    if not hwnd:
        print("[FAIL] 未找到游戏窗口")
        return 1

    info = B.window_bbox(hwnd)
    rec["window_bbox"] = list(info)
    rec["window_wh"] = [info[2] - info[0], info[3] - info[1]]
    print(f"窗口几何: {info}  -> {rec['window_wh'][0]}x{rec['window_wh'][1]}")

    # 客户区与 DPI
    import ctypes
    from ctypes import wintypes
    rc = wintypes.RECT()
    ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rc))
    rec["client_wh"] = [rc.right - rc.left, rc.bottom - rc.top]
    print(f"客户区: {rec['client_wh'][0]}x{rec['client_wh'][1]}")
    try:
        dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
        rec["dpi"] = dpi
        print(f"DPI: {dpi}")
    except Exception:
        pass
    sw = ctypes.windll.user32.GetSystemMetrics(0)
    sh = ctypes.windll.user32.GetSystemMetrics(1)
    rec["screen"] = [sw, sh]
    print(f"屏幕: {sw}x{sh}")

    time.sleep(args.wait)
    if not args.no_nav:
        B.focus_game(hwnd)
    for i in range(args.shots):
        m = B.grab(hwnd, shots / f"{args.tag}_{stamp}_s{i}.png")
        rec.setdefault("grabs", []).append(m)
        print(f"抓图 s{i}: {m['width']}x{m['height']} {m['bytes']}B md5={m['md5'][:10]} "
              f"colors={m['unique_colors_256']} var={m['luma_variance']}")
        time.sleep(2.0)

    out = shots / f"{args.tag}_{stamp}_recon.json"
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print("记录:", out)

    if not args.keep:
        B.kill_game()
    else:
        print("游戏进程保留 (pid=%d hwnd=%d)" % (pid, hwnd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
