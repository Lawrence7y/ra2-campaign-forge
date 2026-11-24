#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-C 目标A：把已激活 ghost 放到目标格，采集三重佐证（额度扣款+owner+格链出现该对象）。
流程（可选先点图标下单）：before -> (下单扣款+等ready+再点图标拿起ghost) -> hover绿框截图 -> 点击 -> after验证。
只读内存 + 合成输入；不写进程内存/不注入。
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
ICON = (2328, 480)
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


def stable_credit(m, ph, tries=10, gap=0.22):
    prev = None; st = 0
    for _ in range(tries):
        cur = m.u32(ph + 0x30C)
        if cur == prev:
            st += 1
            if st >= 2:
                return cur
        else:
            st = 0
        prev = cur
        time.sleep(gap)
    return m.u32(ph + 0x30C)


def player_nap(m, ph):
    return [o for o in C.napowr_objects(m, ph) if o["is_player"]]


def placed_nap(m, ph):
    return [o for o in player_nap(m, ph) if o["o1_81"] == 0 and o["o2_74"] == 1 and o["valid"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tx", type=int, required=True)
    ap.add_argument("--ty", type=int, required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--order", action="store_true", help="click build icon to start order (deduct 600)")
    ap.add_argument("--no-pickup", action="store_true", help="skip 2nd icon click (ghost already active)")
    ap.add_argument("--ready-wait", type=float, default=2.5)
    a = ap.parse_args()

    pid = W.pid_of(); m = W.Mem(pid); ph = P.player_house(m)
    rec = {"tag": a.tag, "ts_start": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "pid": pid, "ph": hex(ph), "target_screen": [a.tx, a.ty]}

    before_credit = stable_credit(m, ph)
    before_placed = {o["obj"] for o in placed_nap(m, ph)}
    rec["before"] = {"credit": before_credit, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                     "placed_objs": sorted(before_placed),
                     "napowr": player_nap(m, ph)}

    # optional: start a new build order (deduct 600 + limbo)
    if a.order:
        ok, info = click_client(pid, *ICON, "left")
        rec["order_click"] = {"ok": ok, "info": info, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        time.sleep(0.4)
        credit_after_order = stable_credit(m, ph)
        rec["order_click"]["credit_after"] = credit_after_order
        rec["order_click"]["deduct"] = (credit_after_order == before_credit - 600)
        # wait for ready (limbo o1=1 persists), then pick up ghost
        time.sleep(a.ready_wait)
        if not a.no_pickup:
            ok2, info2 = click_client(pid, *ICON, "left")
            rec["pickup_click"] = {"ok": ok2, "info": info2, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
            time.sleep(0.35)
    elif not a.no_pickup:
        # pick up existing ready ghost
        ok2, info2 = click_client(pid, *ICON, "left")
        rec["pickup_click"] = {"ok": ok2, "info": info2, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        time.sleep(0.35)

    # hover target -> green screenshot
    move_client(pid, a.tx, a.ty); time.sleep(0.26)
    force_foreground(game_hwnd(pid)); time.sleep(0.08)
    img = ImageGrab.grab(all_screens=False)
    red, green = colors(img, a.tx, a.ty)
    hov = a.tag + "_hover.png"; img.save(os.path.join(EVID, hov))
    rec["hover"] = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "red": red, "green": green,
                    "shot": hov, "credit": m.u32(ph + 0x30C)}

    # click to place
    u32 = ctypes.windll.user32
    if u32.GetForegroundWindow() != game_hwnd(pid):
        force_foreground(game_hwnd(pid)); time.sleep(0.12)
    u32.SetCursorPos(a.tx, a.ty); time.sleep(0.06)
    u32.mouse_event(0x0002, 0, 0, 0, 0); time.sleep(0.10)
    u32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(1.2)
    aft = ImageGrab.grab(all_screens=False)
    aftshot = a.tag + "_after.png"; aft.save(os.path.join(EVID, aftshot))

    after_credit = stable_credit(m, ph)
    after_placed = placed_nap(m, ph)
    after_all = player_nap(m, ph)
    new_placed = [o for o in after_placed if o["obj"] not in before_placed]
    rec["after"] = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "credit": after_credit,
                    "shot": aftshot, "placed_objs": sorted(o["obj"] for o in after_placed),
                    "napowr": after_all}

    # triple attestation
    triple = None
    if new_placed:
        o = new_placed[0]
        # verify object appears in its own target cell chain
        in_chain = (o["obj"] in o["nodesA"]) or (o["obj"] in o["nodesB"])
        triple = {
            "obj": o["obj"], "owner": o["owner"], "owner_is_player": o["is_player"],
            "o1_81": o["o1_81"], "o2_74": o["o2_74"], "cellX": o["cellX"], "cellY": o["cellY"],
            "cell": o["cell"], "valid": o["valid"],
            "in_cell_chain": in_chain, "lenA": o["lenA"], "lenB": o["lenB"],
            "nodesA": o["nodesA"], "nodesB": o["nodesB"],
            "credit_before_order": before_credit,
            "credit_after_order": rec.get("order_click", {}).get("credit_after"),
        }
        triple["attested"] = bool(triple["owner_is_player"] and triple["valid"] and in_chain
                                  and triple["o1_81"] == 0 and triple["o2_74"] == 1)
    rec["triple"] = triple
    rec["signals"] = {"red": red, "green": green, "new_placed": [o["obj"] for o in new_placed],
                      "credit_before": before_credit, "credit_after": after_credit,
                      "attested": bool(triple and triple["attested"])}

    out = os.path.join(EVID, a.tag + ".json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps({"tag": a.tag, "signals": rec["signals"],
                      "triple": triple}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
