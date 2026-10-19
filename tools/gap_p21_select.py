#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gap_p21_select.py — 在地图浏览器里选中指定行（ZC-GAP-P21 A3 前置）。

本构建实测：滚动条箭头必须长按（hold≈0.6s≈5 行）；▲(355,94) ▼(352,295)。
列举行：x∈[200,350]，首行中心 y≈92，行高≈19.1；点 (250, row_center)。
浏览器按钮：使用地圖(720,180) / 取消(720,560)。

用法：
  python tools/gap_p21_select.py --holds 15 --row-y 250           # 滚动后截图+点选+使用
  python tools/gap_p21_select.py --holds 15 --only-shot           # 只滚动+截图（不定点）
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
USE = (720, 180)


def nav_to_setup(hwnd):
    B.focus_game(hwnd)
    time.sleep(18)
    B.press_key(0x1B); time.sleep(1.2)
    B.press_key(0x1B); time.sleep(2.5)
    B.send_click(hwnd, 700, 218); time.sleep(3.0)
    assert B.verify_screen(hwnd, "sp_submenu")["ok"], "未到單人遊戲子菜单"
    B.send_click(hwnd, 700, 304); time.sleep(9.0)
    assert B.verify_screen(hwnd, "skirmish_setup")["ok"], "未到遭遇战设置屏"


ROW_X0, ROW_X1 = 200, 352     # 行文本列
ROW_Y0, ROW_H, ROW_N = 84.0, 19.1, 11   # 首行顶 y、行高、可见行数


def row_text_mask(im, row: int) -> list[bool]:
    """取某行文本列的『亮字像素』掩码（用于行间同名比对）。"""
    y0 = int(ROW_Y0 + row * ROW_H)
    px = im.load()
    mask = []
    for y in range(y0 + 2, int(y0 + ROW_H) - 2):
        for x in range(ROW_X0, ROW_X1):
            r, g, b = px[x, y]
            mask.append((r > 180 and g > 150 and b < 130) or (r > 200 and g > 200 and b > 200))
    return mask


def find_u0800_row(png: Path) -> dict:
    """定位 [2] 0LoadBench U800 行：找长度为 4 的连续同名行块（Urban Rush×4），其下一行即 U800。
    返回 {'row': idx, 'y': 行中心y, 'runs': [...]}。"""
    from PIL import Image
    im = Image.open(png).convert("RGB")
    masks = [row_text_mask(im, i) for i in range(ROW_N)]
    runs = []
    i = 0
    while i < ROW_N:
        j = i
        while j + 1 < ROW_N and _same(masks[j + 1], masks[i]):
            j += 1
        runs.append((i, j, j - i + 1))
        i = j + 1
    cand = [r for r in runs if r[2] == 4 and r[1] + 1 < ROW_N]
    if not cand:
        return {"ok": False, "runs": runs}
    r = cand[0]
    u800_row = r[1] + 1
    return {"ok": True, "row": u800_row,
            "y": int(ROW_Y0 + (u800_row + 0.5) * ROW_H),
            "runs": runs}


def _same(a: list[bool], b: list[bool]) -> bool:
    """同名行判据：实测同名（Urban Rush×4）两两 diff ≤120，异名 ≥245（掩码 2280 位）。
    阈值取 200：同名过、异名拦。"""
    if len(a) != len(b):
        return False
    diff = sum(1 for x, y in zip(a, b) if x != y)
    return diff <= 200


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--holds", type=int, default=15)
    ap.add_argument("--hold", type=float, default=0.6)
    ap.add_argument("--row-y", type=float, default=None)
    ap.add_argument("--auto-u800", action="store_true", help="图内自动定位 U800 行并点选")
    ap.add_argument("--only-shot", action="store_true")
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

    rec = {"tag": tag, "pid": pid, "holds": args.holds}
    if args.holds > 0:
        B.send_click(hwnd, UP[0], UP[1], hold=min(4.0, args.holds * args.hold + 1.0)); time.sleep(1.0)
        for _ in range(args.holds):
            B.send_click(hwnd, DN[0], DN[1], hold=args.hold)
            time.sleep(0.5)
        time.sleep(0.8)
    p = OUT_DIR / f"select_browser_{tag}.png"
    m = B.grab(hwnd, p)
    rec["browser_md5"] = m["md5"]
    rec["browser_shot"] = str(p)
    print(f"[browser] md5={m['md5'][:12]} bytes={m['bytes']}")

    if not args.only_shot and (args.row_y is not None or args.auto_u800):
        if args.auto_u800:
            loc = find_u0800_row(p)
            rec["u800_locate"] = loc
            print("[locate]", json.dumps(loc, ensure_ascii=False))
            if not loc.get("ok"):
                B.kill_game()
                print("[FAIL] 未定位到 U800 行（ Urban Rush×4 行块未出现或 U800 被截断）")
                return 4
            args.row_y = loc["y"]
        B.send_click(hwnd, 250, int(args.row_y)); time.sleep(1.2)
        p2 = OUT_DIR / f"select_clicked_{tag}.png"
        m2 = B.grab(hwnd, p2)
        rec["clicked_md5"] = m2["md5"]
        rec["clicked_shot"] = str(p2)
        B.send_click(hwnd, USE[0], USE[1]); time.sleep(3.0)     # 使用地圖
        p3 = OUT_DIR / f"select_setup_{tag}.png"
        m3 = B.grab(hwnd, p3)
        rec["setup_md5"] = m3["md5"]
        rec["setup_shot"] = str(p3)
        print(f"[setup] md5={m3['md5'][:12]} bytes={m3['bytes']}")

    B.kill_game()
    (OUT_DIR / f"select_{tag}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[json]", OUT_DIR / f"select_{tag}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
