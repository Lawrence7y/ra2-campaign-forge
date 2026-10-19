#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bench_live.py — 附着到运行中的 gamemd.exe 做实时交互（省去反复启动的 30s+）。

与 bench_ingame.py 的区别：不启动/不关闭游戏，纯附着。用于快速校准坐标与验证点击。
（出生点：先 `python tools/bench_ingame.py --scene nav_check --keep` 或直接跑 --launch）

用法：
  python tools/bench_live.py --launch                       # 启动并进入主菜单后保留
  python tools/bench_live.py --plan "shot:a,click:700:218,wait:2,shot:b,banner"
  python tools/bench_live.py --banner                       # 只打印当前标题横幅指纹
  python tools/bench_live.py --crop 648:0:800:42 --out c.png
"""
from __future__ import annotations

import argparse
import ctypes as c2
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_replay as B        # noqa: E402
import bench_ingame as I        # noqa: E402
from bench_shot import find_game_hwnd, capture  # noqa: E402

LW, LH = 800, 600


def get_hwnd() -> int:
    hwnd = find_game_hwnd()
    if not hwnd:
        # 退化：用 bench_replay 的枚举
        import subprocess
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq gamemd.exe", "/FO", "CSV", "/NH"],
                             capture_output=True, text=True, errors="replace").stdout
        for line in out.splitlines():
            parts = [p.strip('"') for p in line.split('","')]
            if len(parts) >= 2 and parts[0].lower().startswith("gamemd"):
                hwnd = B.find_game_hwnd(int(parts[1]))
                if hwnd:
                    return hwnd
        raise SystemExit("[FAIL] 未找到运行中的 gamemd.exe")
    return hwnd


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="bench_live")
    ap.add_argument("--launch", action="store_true", help="先启动游戏并跳过开场")
    ap.add_argument("--boot-wait", type=float, default=26.0)
    ap.add_argument("--plan", default="")
    ap.add_argument("--banner", action="store_true")
    ap.add_argument("--crop", default=None, help="x0:y0:x1:y1（800x600 逻辑坐标）")
    ap.add_argument("--out", default=None)
    ap.add_argument("--telemetry", action="store_true")
    ap.add_argument("--state", action="store_true", help="打印 CurrentFrame / 机动单位数")
    ap.add_argument("--shots-dir", default=None)
    args = ap.parse_args(argv)

    if args.launch:
        B.kill_game()
        pid = B.launch()
        hwnd = None
        t_end = time.time() + 20
        while time.time() < t_end and not hwnd:
            hwnd = I and B.find_game_hwnd(pid)
            time.sleep(0.5)
        print(f"[live] 启动 pid={pid} hwnd={hwnd}，等待 {args.boot_wait:.0f}s")
        time.sleep(args.boot_wait)
        B.focus_game(hwnd)
        B.press_key(0x1B); time.sleep(1.2)
        B.press_key(0x1B); time.sleep(2.0)
        B.focus_game(hwnd)
    else:
        hwnd = get_hwnd()

    shots = Path(args.shots_dir) if args.shots_dir else (B.SHOTS / "live")
    shots.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%H%M%S")

    if args.banner:
        print("banner fp:", I.banner_fp(hwnd))
    if args.state:
        pid = None
        import subprocess
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq gamemd.exe", "/FO", "CSV", "/NH"],
                             capture_output=True, text=True, errors="replace").stdout
        for line in out.splitlines():
            parts = [p.strip('"') for p in line.split('","')]
            if len(parts) >= 2 and parts[0].lower().startswith("gamemd"):
                pid = int(parts[1]); break
        if pid:
            proc = B.open_proc(pid)
            mon = B.BattleMonitor(proc)
            print(f"pid={pid} CurrentFrame={mon.frame()} 机动单位={mon.mobile_count()}")
    if args.crop:
        x0, y0, x1, y1 = [int(v) for v in args.crop.split(":")]
        l, t, r, b = B.window_bbox(hwnd)
        cx0 = l + int(x0 / LW * (r - l)); cx1 = l + int(x1 / LW * (r - l))
        cy0 = t + int(y0 / LH * (b - t)); cy1 = t + int(y1 / LH * (b - t))
        m = capture(cx0, cy0, max(cx1 - cx0, 4), max(cy1 - cy0, 4),
                    Path(args.out or (shots / f"crop_{stamp}.png")))
        print(json.dumps(m, ensure_ascii=False))
    if args.telemetry:
        for l in B.parse_telemetry(B.GAME_DIR)[-3:]:
            print("TELEMETRY:", l)

    if args.plan:
        for tok in [t.strip() for t in args.plan.split(",") if t.strip()]:
            parts = tok.split(":")
            act = parts[0]
            if act == "wait":
                time.sleep(float(parts[1]))
            elif act == "shot":
                m = B.grab(hwnd, shots / f"{stamp}_{parts[1]}.png")
                print(f"  shot {parts[1]:16s} {m['bytes']:>7}B md5={m['md5'][:10]} "
                      f"colors={m['unique_colors_256']} var={m['luma_variance']}")
            elif act == "click":
                x, y = int(parts[1]), int(parts[2])
                before = I.banner_fp(hwnd)
                changed = False
                tries = int(parts[3]) if len(parts) > 3 else 5
                for i in range(tries):
                    B.focus_game(hwnd)
                    B.send_click(hwnd, x, y, lw=LW, lh=LH)
                    time.sleep(2.5)
                    now = I.banner_fp(hwnd)
                    if now != before:
                        print(f"  click ({x},{y}) 第{i + 1}次生效 banner {before} -> {now}")
                        changed = True
                        break
                    print(f"  click ({x},{y}) 第{i + 1}次未生效")
                    time.sleep(0.8)
                if not changed:
                    print(f"  [WARN] click ({x},{y}) {tries} 次均未生效（画面未切换）")
            elif act == "key":
                km = {"esc": 0x1B, "enter": 0x0D, "space": 0x20}
                vk = km[parts[1]] if parts[1] in km else int(parts[1], 0)
                B.focus_game(hwnd)
                B.press_key(vk)
                print(f"  key {parts[1]} banner->{I.banner_fp(hwnd)}")
            elif act == "banner":
                print(f"  banner fp: {I.banner_fp(hwnd)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
