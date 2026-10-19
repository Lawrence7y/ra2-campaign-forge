#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bench_ingame.py — Z-1 真机证据采集驱动（菜单导航 + 对局内采集 + 存档往返）。

设计要点（针对前几轮失败模式）：
  1. **导航必须自证**：每次点击后比对「标题横幅区」指纹（800x600 下 (650,0,800,42)
     显示当前画面名：主選單/單人遊戲/戰役/遭遇戰…），未变化即视为该步失败 → 重试；
     首次点击常被 Windows「点击激活」吞掉，因此重试是必需的而非可选。
  2. **对局必须自证**：CurrentFrame(0xA8ED84) 推进 ≥3 fps + 机动单位数 ∈ [0.5×,1.6×] 期望。
  3. **截图 MD5 同批次互异**（证据标准 v2）：ShotSession 内置去重 + 重试。
  4. 分辨率固定 800x600（本机引擎实际模式；PROTOCOL.md 已声明）。

用法：
  python tools/bench_ingame.py --scene skirmish_entry      # 进遭遇战并留图（逐步）
  python tools/bench_ingame.py --scene load_list           # 载入存档列表留图
  python tools/bench_ingame.py --scene nav_check           # 仅校验导航基元是否可用
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_replay as B  # noqa: E402

LW, LH = 800, 600
BANNER = (648, 0, 800, 42)      # 标题横幅（含画面名文字）

# 已校准坐标（800x600，繁中 UI；来源 out/loadbench/shots/probe/）
MAIN_MENU = {"單人遊戲": (700, 218), "網際網路": (700, 260), "網路": (700, 300),
             "動畫及製作人員": (700, 340), "選項": (700, 383), "退出遊戲": (700, 545)}
SP_MENU = {"新戰役": (700, 218), "載入儲存遊戲": (700, 260), "遭遇戰": (700, 302),
           "主選單": (700, 546)}


def banner_fp(hwnd: int) -> str:
    """标题横幅区指纹（sha256 前 12 位）：画面名文字变化 → 画面已切换。"""
    from PIL import Image
    import ctypes as c2
    gdi32 = c2.WinDLL("gdi32")
    l, t, r, b = B.window_bbox(hwnd)
    x0, y0, x1, y1 = BANNER
    x0 = l + int(x0 / LW * (r - l)); x1 = l + int(x1 / LW * (r - l))
    y0 = t + int(y0 / LH * (b - t)); y1 = t + int(y1 / LH * (b - t))
    w, h = max(x1 - x0, 4), max(y1 - y0, 4)
    sdc = B.user32.GetDC(0)
    mdc = gdi32.CreateCompatibleDC(sdc)
    hbmp = gdi32.CreateCompatibleBitmap(sdc, w, h)
    gdi32.SelectObject(mdc, hbmp)
    gdi32.BitBlt(mdc, 0, 0, w, h, sdc, x0, y0, 0x00CC0020)

    class BMIH(c2.Structure):
        _fields_ = [("biSize", c2.c_ulong), ("biWidth", c2.c_long), ("biHeight", c2.c_long),
                    ("biPlanes", c2.c_ushort), ("biBitCount", c2.c_ushort), ("biCompression", c2.c_ulong),
                    ("biSizeImage", c2.c_ulong), ("biXPPM", c2.c_long), ("biYPPM", c2.c_long),
                    ("biClrUsed", c2.c_ulong), ("biClrImportant", c2.c_ulong)]

    bmi = BMIH(c2.sizeof(BMIH), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = c2.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mdc, hbmp, 0, h, buf, c2.byref(bmi), 0)
    img = Image.frombuffer("RGB", (w, h), buf.raw, "raw", "BGRX", 0, 1)
    gdi32.DeleteObject(hbmp); gdi32.DeleteDC(mdc); B.user32.ReleaseDC(0, sdc)
    return hashlib.sha256(img.tobytes()).hexdigest()[:12]


def nav_click(hwnd: int, xy: tuple[int, int], *, name: str = "", wait: float = 2.5,
              retries: int = 5, shots_dir: Path | None = None, tag: str = "",
              expect_change: bool = True) -> bool:
    """自证式点击：横幅指纹变化才算成功；未变化重试（首击被吞是常态）。"""
    x, y = xy
    before = banner_fp(hwnd)
    for i in range(retries):
        B.focus_game(hwnd)
        B.send_click(hwnd, x, y, lw=LW, lh=LH)
        time.sleep(wait)
        after = banner_fp(hwnd)
        ok = (after != before)
        print(f"  [nav] {name or f'({x},{y})'} 尝试 {i + 1}/{retries} "
              f"横幅 {before} -> {after} {'OK' if ok else '未变化'}")
        if shots_dir is not None and i == 0:
            B.grab(hwnd, shots_dir / f"{tag}_nav_{name or f'{x}_{y}'}_a{i}.png")
        if ok or not expect_change:
            return True
        time.sleep(0.8)
    return False


def enter_main_menu(pid: int, hwnd: int, *, boot_wait: float = 26.0) -> None:
    time.sleep(boot_wait)
    B.focus_game(hwnd)
    B.press_key(0x1B); time.sleep(1.2)
    B.press_key(0x1B); time.sleep(2.0)
    B.focus_game(hwnd)


def scene_nav_check(hwnd: int, shots: Path, tag: str):
    """校验导航基元：主選單 -> 單人遊戲 -> 主選單，两次都应成功。"""
    r = []
    r.append(("->單人遊戲", nav_click(hwnd, SP_MENU and MAIN_MENU["單人遊戲"], name="mainmenu_sp",
                                      shots_dir=shots, tag=tag)))
    r.append(("->主選單", nav_click(hwnd, SP_MENU["主選單"], name="sp_back",
                                    shots_dir=shots, tag=tag)))
    return r


def scene_skirmish_entry(hwnd: int, shots: Path, tag: str, ss: B.ShotSession):
    """主選單 -> 單人遊戲 -> 遭遇戰 -> 大厅留图。"""
    log = []
    log.append(("單人遊戲", nav_click(hwnd, MAIN_MENU["單人遊戲"], name="sp",
                                      shots_dir=shots, tag=tag)))
    log.append(("遭遇戰", nav_click(hwnd, SP_MENU["遭遇戰"], name="skirmish",
                                    shots_dir=shots, tag=tag, wait=6.0)))
    time.sleep(6.0)
    ss.step(hwnd, shots / f"{tag}_lobby.png")
    return log


def scene_load_list(hwnd: int, shots: Path, tag: str, ss: B.ShotSession):
    log = []
    log.append(("單人遊戲", nav_click(hwnd, MAIN_MENU["單人遊戲"], name="sp",
                                      shots_dir=shots, tag=tag)))
    log.append(("載入儲存遊戲", nav_click(hwnd, SP_MENU["載入儲存遊戲"], name="load",
                                          shots_dir=shots, tag=tag, wait=6.0)))
    time.sleep(4.0)
    ss.step(hwnd, shots / f"{tag}_loadlist.png")
    return log


SCENES = {"nav_check": scene_nav_check, "skirmish_entry": scene_skirmish_entry,
          "load_list": scene_load_list}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="bench_ingame")
    ap.add_argument("--scene", default="nav_check", choices=sorted(SCENES))
    ap.add_argument("--tag", default=None)
    ap.add_argument("--boot-wait", type=float, default=26.0)
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args(argv)

    tag = args.tag or args.scene
    shots = B.SHOTS / "ingame"
    shots.mkdir(parents=True, exist_ok=True)

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
    print(f"[ingame] pid={pid} hwnd={hwnd}")
    enter_main_menu(pid, hwnd, boot_wait=args.boot_wait)

    ss = B.ShotSession()
    out = {"pid": pid, "hwnd": hwnd, "scene": args.scene,
           "ts": datetime.now().isoformat(timespec="seconds")}
    try:
        log = SCENES[args.scene](hwnd, shots, tag, ss) if args.scene != "nav_check" \
            else scene_nav_check(hwnd, shots, tag)
        out["nav_log"] = [{"step": s, "ok": bool(o)} for s, o in log]
        print("导航结果:", out["nav_log"])
        out["shot_session"] = ss.snapshot()
    finally:
        p = shots / f"{tag}_ingame.json"
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print("记录:", p)
        if not args.keep:
            B.kill_game()
        else:
            print(f"保留 pid={pid} hwnd={hwnd}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
