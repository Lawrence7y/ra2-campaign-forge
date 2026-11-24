#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-C 目标B：单次『引擎拒绝放置』完整状态快照采集器。
流程：before快照 -> 点NAPOWR图标(扣款+limbo) -> hover非法格(红圈截图) -> 点击 -> after快照。
全部只读内存 + 合成输入(click_client)；不写进程内存/不注入/不改ra2youli。
"""
import argparse
import ctypes
import json
import os
import sys
import time
from PIL import ImageGrab

import w177_core as W
import wb_probe as P
import wc_probe as C
from w177_click import click_client, move_client, force_foreground, game_hwnd

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")
CREDIT_OFF = 0x30C
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass


def cursor_colors(img, sx, sy, rad=60):
    im = img.convert("RGB"); px = im.load(); w, h = im.size
    red = green = 0
    for y in range(max(0, sy - rad), min(h, sy + rad)):
        for x in range(max(0, sx - rad), min(w, sx + rad)):
            r, g, b = px[x, y]
            if r > 150 and g < 90 and b < 90:
                red += 1
            if g > 140 and r < 120 and b < 120:
                green += 1
    return red, green


def snap_with_targets(m, targets):
    return C.full_snapshot(m, targets=targets)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--icon-x", type=int, default=2328)
    ap.add_argument("--icon-y", type=int, default=480)
    ap.add_argument("--tx", type=int, required=True, help="target screen X (invalid cell)")
    ap.add_argument("--ty", type=int, required=True, help="target screen Y")
    ap.add_argument("--tcell", default=None, help="target map cell as CX,CY for chain snapshot")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--no-click-icon", action="store_true")
    a = ap.parse_args()

    targets = []
    if a.tcell:
        tx, ty = [int(v) for v in a.tcell.split(",")]
        targets = [(tx, ty)]

    pid = W.pid_of()
    m = W.Mem(pid)
    ts0 = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    rec = {"tag": a.tag, "ts_start": ts0, "pid": pid,
           "icon": [a.icon_x, a.icon_y], "target_screen": [a.tx, a.ty],
           "target_cell": a.tcell}

    # BEFORE
    rec["before"] = snap_with_targets(m, targets)
    rec["before"]["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    # enter placement mode via icon click (deduct 600 + limbo)
    if not a.no_click_icon:
        ok_i, info_i = click_client(pid, a.icon_x, a.icon_y, "left")
        rec["icon_click"] = {"ok": ok_i, "info": info_i}
        time.sleep(0.35)
    else:
        rec["icon_click"] = {"skipped": True}
    rec["after_icon"] = snap_with_targets(m, targets)
    rec["after_icon"]["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    # hover target cell -> red circle screenshot
    move_client(pid, a.tx, a.ty)
    time.sleep(0.30)
    force_foreground(game_hwnd(pid))
    time.sleep(0.12)
    img = ImageGrab.grab(all_screens=False)
    red, green = cursor_colors(img, a.tx, a.ty)
    img.save(os.path.join(EVID, a.tag + "_hover.png"))
    rec["hover"] = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "red": red, "green": green,
                    "shot": a.tag + "_hover.png",
                    "snapshot": snap_with_targets(m, targets)}

    # click target (engine reject expected)
    u32 = ctypes.windll.user32
    if u32.GetForegroundWindow() != game_hwnd(pid):
        force_foreground(game_hwnd(pid)); time.sleep(0.2)
    u32.SetCursorPos(a.tx, a.ty)
    time.sleep(0.1)
    u32.mouse_event(0x0002, 0, 0, 0, 0); time.sleep(0.10)
    u32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(1.0)
    img2 = ImageGrab.grab(all_screens=False)
    img2.save(os.path.join(EVID, a.tag + "_after.png"))
    rec["after_click"] = snap_with_targets(m, targets)
    rec["after_click"]["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    rec["after_click"]["shot"] = a.tag + "_after.png"

    # derived signals
    b = rec["before"]["credit_30C"]
    ai = rec["after_icon"]["credit_30C"]
    ac = rec["after_click"]["credit_30C"]
    ph = rec["before"]["playerHouse"]
    def limbo(s):
        return [o for o in s["napowr"] if o["is_player"] and o["o1_81"] == 1]
    def placed(s):
        return [o for o in s["napowr"] if o["is_player"] and o["o1_81"] == 0 and o["o2_74"] == 1 and o["valid"]]
    rec["signals"] = {
        "credit_before": b, "credit_after_icon": ai, "credit_after_click": ac,
        "deduct_on_icon": (ai == b - 600) if b is not None else None,
        "refund_after_click": (ac == b) if b is not None else None,
        "limbo_before": len(limbo(rec["before"])),
        "limbo_after_icon": len(limbo(rec["after_icon"])),
        "limbo_after_click": len(limbo(rec["after_click"])),
        "placed_before": len(placed(rec["before"])),
        "placed_after": len(placed(rec["after_click"])),
        "red": red, "green": green,
    }

    out = os.path.join(EVID, a.tag + ".json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps({"tag": a.tag, "signals": rec["signals"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
