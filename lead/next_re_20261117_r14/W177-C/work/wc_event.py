#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-C 目标B：在 ghost 已激活时捕获一次『引擎拒绝放置』完整状态快照。
用法：先确保 ghost 激活（ready 图标第二次点击），再运行本脚本。
流程：before -> hover 非法格(红圈截图+时间戳) -> click -> after；全字段只读。
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
from w177_click import move_client, force_foreground, game_hwnd

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass


def colors(img, sx, sy, rad=70):
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


def stable_snap(m, targets, tries=8, gap=0.25):
    """等 credit 稳定后取快照（+0x30C 动画逼近真值）。"""
    prev = None
    stable = 0
    for _ in range(tries):
        cur = m.u32(P.player_house(m) + 0x30C)
        if cur == prev:
            stable += 1
            if stable >= 2:
                break
        else:
            stable = 0
        prev = cur
        time.sleep(gap)
    return C.full_snapshot(m, targets=targets)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tx", type=int, required=True)
    ap.add_argument("--ty", type=int, required=True)
    ap.add_argument("--tcell", default=None, help="target map cell CX,CY")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--no-click", action="store_true", help="hover only; skip click")
    ap.add_argument("--right", action="store_true", help="right-click instead of left")
    a = ap.parse_args()
    targets = []
    if a.tcell:
        cx, cy = [int(v) for v in a.tcell.split(",")]
        targets = [(cx, cy)]

    pid = W.pid_of()
    m = W.Mem(pid)
    rec = {"tag": a.tag, "ts_start": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "target_screen": [a.tx, a.ty], "target_cell": a.tcell,
           "note": "ghost active before event; 2nd icon click already done"}

    rec["before"] = stable_snap(m, targets)
    rec["before"]["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    # hover target
    move_client(pid, a.tx, a.ty); time.sleep(0.28)
    force_foreground(game_hwnd(pid)); time.sleep(0.10)
    img = ImageGrab.grab(all_screens=False)
    red, green = colors(img, a.tx, a.ty)
    hov_shot = a.tag + "_hover.png"
    img.save(os.path.join(EVID, hov_shot))
    rec["hover"] = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "red": red, "green": green, "shot": hov_shot,
                    "snapshot": C.full_snapshot(m, targets=targets)}

    # click target
    u32 = ctypes.windll.user32
    if u32.GetForegroundWindow() != game_hwnd(pid):
        force_foreground(game_hwnd(pid)); time.sleep(0.15)
    u32.SetCursorPos(a.tx, a.ty); time.sleep(0.08)
    if not a.no_click:
        if a.right:
            u32.mouse_event(0x0008, 0, 0, 0, 0); time.sleep(0.10)
            u32.mouse_event(0x0010, 0, 0, 0, 0)
        else:
            u32.mouse_event(0x0002, 0, 0, 0, 0); time.sleep(0.10)
            u32.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(1.2)
    rec["click"] = {"button": "right" if a.right else ("none" if a.no_click else "left"),
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    img2 = ImageGrab.grab(all_screens=False)
    aft_shot = a.tag + "_after.png"
    img2.save(os.path.join(EVID, aft_shot))
    rec["after"] = stable_snap(m, targets)
    rec["after"]["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    rec["after"]["shot"] = aft_shot

    # signals
    def pnap(s):
        return [o for o in s["napowr"] if o["is_player"]]
    def limbo(s):
        return [o for o in pnap(s) if o["o1_81"] == 1]
    def placed(s):
        return [o for o in pnap(s) if o["o1_81"] == 0 and o["o2_74"] == 1 and o["valid"]]
    b, af = rec["before"], rec["after"]
    rec["signals"] = {
        "credit_before": b["credit_30C"], "credit_after": af["credit_30C"],
        "credit_delta": (af["credit_30C"] - b["credit_30C"]) if b["credit_30C"] is not None else None,
        "refund_600": (af["credit_30C"] == b["credit_30C"] + 600) if b["credit_30C"] is not None else None,
        "limbo_before": [(o["obj"], o["o1_81"], o["o2_74"], o["canplace_1AC_u8"], o["canplace_1AC_u32"]) for o in limbo(b)],
        "limbo_after": [(o["obj"], o["o1_81"], o["o2_74"], o["canplace_1AC_u8"], o["canplace_1AC_u32"]) for o in limbo(af)],
        "placed_before": [o["obj"] for o in placed(b)],
        "placed_after": [o["obj"] for o in placed(af)],
        "new_placed": [o["obj"] for o in placed(af) if o["obj"] not in {p["obj"] for p in placed(b)}],
        "red": red, "green": green,
        "target_before": b.get("targets"),
        "target_after": af.get("targets"),
    }
    out = os.path.join(EVID, a.tag + ".json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps({"tag": a.tag, "signals": rec["signals"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
