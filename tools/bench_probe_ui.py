#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bench_probe_ui.py — 真机 UI 探查：一次启动内按剧本点击并逐步留图（只读，不改 config）。

用途：校准菜单/建造栏坐标。每次点击后立即留图，便于事后逐帧核对。
分辨率基准：800x600（本机引擎实际模式，见 out/loadbench/PROTOCOL.md）。

用法：
  python tools/bench_probe_ui.py --plan single_player
  python tools/bench_probe_ui.py --plan "esc,esc,wait:3,shot:a,click:700:218,wait:3,shot:b"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_replay as B  # noqa: E402

LW, LH = 800, 600

# 剧本：名称 -> [(动作, 参数...)]；动作 wait/shot/click/key
PLANS: dict[str, list] = {
    # 单机路径：主菜单 -> 單人遊戲 -> 子菜单各处
    "single_player": [
        ("key", "esc", 1.2), ("key", "esc", 2.0), ("wait", 3.0),
        ("shot", "01_mainmenu"),
        ("click", 700, 218), ("wait", 4.0), ("shot", "02_singleplayer"),
        ("click", 700, 215), ("wait", 4.0), ("shot", "03_sp_item1"),
        ("click", 700, 258), ("wait", 4.0), ("shot", "04_sp_item2"),
        ("click", 700, 300), ("wait", 4.0), ("shot", "05_sp_item3"),
        ("click", 700, 345), ("wait", 4.0), ("shot", "06_sp_item4"),
    ],
    # 遭遇战大厅：进入后逐区留图
    "skirmish_lobby": [
        ("key", "esc", 1.2), ("key", "esc", 2.0), ("wait", 3.0),
        ("click", 700, 218), ("wait", 4.0),
        ("click", 700, 300), ("wait", 8.0), ("shot", "10_lobby"),
    ],
}

KEYMAP = {"esc": 0x1B, "enter": 0x0D, "space": 0x20, "tab": 0x09,
          "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27}


def parse_plan(text: str) -> list:
    out = []
    for tok in [t.strip() for t in text.split(",") if t.strip()]:
        m = re.match(r"^(wait|shot|click|key):?(.*)$", tok)
        if not m:
            continue
        act, rest = m.group(1), m.group(2)
        if act == "wait":
            out.append(("wait", float(rest)))
        elif act == "shot":
            out.append(("shot", rest))
        elif act == "key":
            out.append(("key", rest, 1.0))
        elif act == "click":
            parts = rest.split(":")
            out.append(("click", int(parts[0]), int(parts[1])))
    return out


def run(plan: list, shots_dir: Path, tag: str, *, wait_boot: float, keep: bool) -> int:
    shots_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%H%M%S")
    B.kill_game()
    pid = B.launch()
    proc = B.open_proc(pid)
    hwnd = None
    t_end = time.time() + 20
    while time.time() < t_end and not hwnd:
        hwnd = B.find_game_hwnd(pid)
        time.sleep(0.5)
    if not hwnd:
        print("[FAIL] 未找到游戏窗口")
        return 1
    print(f"[probe] pid={pid} hwnd={hwnd} 等待 {wait_boot:.0f}s 使菜单就绪")
    time.sleep(wait_boot)
    B.focus_game(hwnd)

    recs = []

    def snap(name: str):
        m = B.grab(hwnd, shots_dir / f"{tag}_{stamp}_{name}.png")
        recs.append(m)
        print(f"  shot {name:22s} {m['width']}x{m['height']} {m['bytes']:>7}B "
              f"md5={m['md5'][:10]} colors={m['unique_colors_256']} var={m['luma_variance']}")
        return m

    for step in plan:
        act = step[0]
        if act == "wait":
            time.sleep(step[1])
        elif act == "shot":
            snap(step[1])
        elif act == "click":
            print(f"  click ({step[1]},{step[2]})")
            B.focus_game(hwnd)
            B.send_click(hwnd, step[1], step[2], lw=LW, lh=LH)
        elif act == "key":
            vk = KEYMAP.get(step[1].lower())
            print(f"  key {step[1]} ({vk})")
            B.focus_game(hwnd)
            B.press_key(vk, hold=step[2] if len(step) > 2 else 0.05)

    out = shots_dir / f"{tag}_{stamp}_probe.json"
    out.write_text(json.dumps({"stamp": stamp, "pid": pid, "hwnd": hwnd, "shots": recs},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print("记录:", out)
    if keep:
        print("游戏保留 pid=%d hwnd=%d" % (pid, hwnd))
    else:
        B.kill_game()
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="bench_probe_ui")
    ap.add_argument("--plan", default="single_player")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--wait-boot", type=float, default=25.0)
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args(argv)

    plan = PLANS.get(args.plan) or parse_plan(args.plan)
    tag = args.tag or (args.plan if args.plan in PLANS else "custom")
    return run(plan, B.SHOTS / "probe", tag, wait_boot=args.wait_boot, keep=args.keep)


if __name__ == "__main__":
    raise SystemExit(main())
