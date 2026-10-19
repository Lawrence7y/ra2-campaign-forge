#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gap_p21_mapbrowser.py — 打开遭遇战地图浏览器并翻页枚举，定位 GAPP21 行坐标。

布局（800×600，实测自 dlg_left.png 全分辨率判读）：
  列表行 x∈[200,385]；行高 ≈24.5px，首行中心 y≈48（i 行 y≈48+i*24.5）；
  滚动条 x≈405：上箭头 y≈40，下箭头 y≈303，轨道页下翻 y≈200（滑块初始约在 1/3 处）。
翻页：点下箭头 = 单行；点轨道 = 整页。本脚本先轨道页翻、发现目标行后再单行精调。
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
UP_ARROW = (405, 40)
DOWN_ARROW = (405, 303)
TRACK_MID = (405, 200)
ROW_X = 300           # 行中心（点选地图）
ROW0_Y = 48.0
ROW_H = 24.5


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
    ap.add_argument("--pages", type=int, default=18)
    ap.add_argument("--page-clicks", type=int, default=1, help="每次翻页点击轨道次数")
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
    rec = {"tag": tag, "pid": pid, "pages": []}
    prev_md5 = None
    for i in range(args.pages):
        p = OUT_DIR / f"mapbrowser_p{i:02d}_{tag}.png"
        m = B.grab(hwnd, p)
        rec["pages"].append({"page": i, "md5": m["md5"], "path": str(p)})
        print(f"[page {i:02d}] md5={m['md5'][:12]} bytes={m['bytes']}")
        if prev_md5 == m["md5"]:
            print("[stop] 页面不再变化（已到列表底）")
            break
        prev_md5 = m["md5"]
        for _ in range(args.page_clicks):
            B.send_click(hwnd, TRACK_MID[0], TRACK_MID[1])
        time.sleep(1.2)
    B.kill_game()
    (OUT_DIR / f"mapbrowser_{tag}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[json]", OUT_DIR / f"mapbrowser_{tag}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
