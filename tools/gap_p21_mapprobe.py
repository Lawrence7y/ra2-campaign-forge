#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gap_p21_mapprobe.py — 定位「打开地图浏览器」的可点击部件（ZC-GAP-P21 A3 UI 排障）

已知：点击 (700,90) 会把当前地图切到下一张（ScenIndex+1），不弹列表。
本脚本依次尝试多个候选位置，每个位置点一次、截图、记录 md5，供人工/自动判读：
  - 若某次点击后画面变成大地图列表模态 ⇒ 那就是浏览器入口
  - 若只是地图名/预览变化 ⇒ 该点是「下一张」循环钮
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "tools"))
import bench_replay as B  # noqa: E402

B.GAME_DIR = PROJECT / "ra2bench"
GAME_DIR = PROJECT / "ra2bench"
OUT_DIR = PROJECT / "out" / "re_work" / "zcode_live" / "gap_p21"

CANDIDATES = [
    ("minimap_center", 740, 25),
    ("mapname_area",   740, 65),
    ("box_topleft",    690, 15),
    ("box_bottomleft", 690, 75),
]


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
    tag = datetime.now().strftime("%H%M%S")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    B.kill_game(); time.sleep(1.5)
    pid = B.launch()
    hwnd = None
    t_end = time.time() + 20
    while time.time() < t_end and not hwnd:
        hwnd = B.find_game_hwnd(pid)
        time.sleep(0.5)
    assert hwnd
    B.focus_game(hwnd)
    nav_to_setup(hwnd)
    rec = {"tag": tag, "pid": pid, "shots": []}
    from bench_shot import capture  # type: ignore
    import ctypes
    sw = ctypes.windll.user32.GetSystemMetrics(0)
    sh = ctypes.windll.user32.GetSystemMetrics(1)
    rec["screen"] = [sw, sh]
    for name, x, y in CANDIDATES:
        B.send_click(hwnd, x, y)
        time.sleep(2.0)
        p = OUT_DIR / f"mapprobe_{name}_{tag}.png"
        m = B.grab(hwnd, p)
        pf = OUT_DIR / f"mapprobe_full_{name}_{tag}.png"
        mf = capture(0, 0, sw, sh, pf)
        rec["shots"].append({"cand": name, "xy": [x, y], "md5": m["md5"], "bytes": m["bytes"],
                              "full_md5": mf.get("md5"), "full_bytes": mf.get("bytes"),
                              "full_path": str(pf)})
        print(f"[probe] {name:16s} ({x},{y}) win_md5={m['md5'][:12]} full_md5={str(mf.get('md5'))[:12]} full_bytes={mf.get('bytes')}")
    B.kill_game()
    (OUT_DIR / f"mapprobe_{tag}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[json]", OUT_DIR / f"mapprobe_{tag}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
