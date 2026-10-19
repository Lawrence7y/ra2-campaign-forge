#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gap_p21_maplist.py — 枚举遭遇战地图浏览器全表，定位 GAPP21 行。

实测结论：本构建的滚动条箭头必须**长按**才滚动（短click不响应；hold=0.6s ≈ 5 行）。
布局（800×600）：列表行 x∈[200,350] 行高≈19px 首行中心 y≈92；▲(355,94) ▼(355,307)；
  行点击目标 x≈250, y=row_center。
流程：开浏览器 → 长按▲到顶 → 逐段长按▼下翻并截图 → 到底（画面不再变化）停止。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "tools"))
import bench_replay as B  # noqa: E402

B.GAME_DIR = PROJECT / "ra2bench"
OUT_DIR = PROJECT / "out" / "re_work" / "zcode_live" / "gap_p21"
UP = (355, 94)
DN = (352, 295)


def nav_to_setup(hwnd):
    B.focus_game(hwnd)
    time.sleep(18)
    B.press_key(0x1B); time.sleep(1.2)
    B.press_key(0x1B); time.sleep(2.5)
    B.send_click(hwnd, 700, 218); time.sleep(3.0)
    assert B.verify_screen(hwnd, "sp_submenu")["ok"], "未到單人遊戲子菜单"
    B.send_click(hwnd, 700, 304); time.sleep(9.0)
    assert B.verify_screen(hwnd, "skirmish_setup")["ok"], "未到遭遇战设置屏"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--hold", type=float, default=0.6, help="每次下翻长按秒数（0.6s≈5 行；短按不滚动）")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    tag = args.tag or datetime.now().strftime("%H%M%S")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    B.kill_game(); time.sleep(1.5)
    pid = B.launch()
    hwnd = None
    t_end = time.time() + 20
    while time.time() < t_end and not hwnd:
        hwnd = B.find_game_hwnd(pid)
        time.sleep(0.5)
    assert hwnd
    nav_to_setup(hwnd)
    B.send_click(hwnd, 700, 304); time.sleep(3.0)     # 自訂戰役 → 地图浏览器

    # 1) 长按▲回顶
    B.send_click(hwnd, UP[0], UP[1], hold=4.0); time.sleep(1.5)
    rec = {"tag": tag, "pid": pid, "shots": []}
    p0 = OUT_DIR / f"mlist_top_{tag}.png"
    m0 = B.grab(hwnd, p0)
    rec["shots"].append({"i": -1, "md5": m0["md5"], "path": str(p0)})
    print(f"[top] md5={m0['md5'][:12]} bytes={m0['bytes']}")

    # 2) 逐段下翻
    prev = m0["md5"]
    for i in range(args.steps):
        B.send_click(hwnd, DN[0], DN[1], hold=args.hold)
        time.sleep(0.9)
        p = OUT_DIR / f"mlist_{i:02d}_{tag}.png"
        m = B.grab(hwnd, p)
        rec["shots"].append({"i": i, "md5": m["md5"], "path": str(p)})
        print(f"[{i:02d}] md5={m['md5'][:12]} bytes={m['bytes']}")
        if m["md5"] == prev:
            print("[stop] 画面不再变化（到底）")
            break
        prev = m["md5"]

    B.kill_game()
    (OUT_DIR / f"mlist_{tag}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[json]", OUT_DIR / f"mlist_{tag}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
