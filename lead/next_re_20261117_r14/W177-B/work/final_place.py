#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最终放置器：进入放置模式后在候选格上 hover，用光标邻域像素统计区分
red-X(禁放) vs green-outline(可放)，仅在判定可放时点击并校验额度/对象/格链。
所有点击/移动经 w177_click（前台+归属校验）。"""
import json
import os
import sys
import time
import ctypes
from PIL import ImageGrab

import w177_core as W
import wb_probe as P
from w177_click import click_client, move_client, force_foreground, game_hwnd

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")
CREDIT_OFF = 0x30C
ctypes.windll.user32.SetProcessDPIAware()


def cursor_colors(img, cx, cy, rad=55):
    im = img.convert("RGB"); px = im.load(); w, h = im.size
    red = green = 0
    for y in range(max(0, cy - rad), min(h, cy + rad)):
        for x in range(max(0, cx - rad), min(w, cx + rad)):
            r, g, b = px[x, y]
            if r > 165 and g < 90 and b < 90:
                red += 1
            if g > 150 and r < 110 and b < 110:
                green += 1
    return red, green


def napowr_state(m, ph):
    out = []
    for i, obj in P.enumerate_buildings(m)[2]:
        b = P.one_building(m, i, obj)
        if b["owner_21C"] == ph and b["type"] == "NAPOWR":
            c = b["cell"]
            out.append({"obj": b["obj_hex"], "o1": b["o1_81"], "o2": b["o2_74"],
                        "cx": c["cellX"], "cy": c["cellY"], "valid": c["valid"],
                        "cell": hex(c["cell"]) if c.get("cell") else None,
                        "chainA": b["chains"]["lenA"], "chainB": b["chains"]["lenB"],
                        "nodesA": b["chains"]["nodesA"], "nodesB": b["chains"]["nodesB"]})
    return out


def main():
    pid = W.pid_of(); m = W.Mem(pid); ph = P.player_house(m)
    rec = {"pid": pid, "ph": hex(ph)}
    # candidate cells: open areas (physical). avoid units near conyard center ~ (1620,550)
    cands = [(2100,250),(2150,300),(2050,250),(2200,350),(1950,250),
             (1900,500),(1950,600),(2050,650),(1800,700),(1700,700),
             (1500,250),(1400,300),(1300,350),(1200,400),
             (2100,700),(2200,600),(2300,500),(1000,400),(1100,650)]
    results = []
    for attempt, (cx, cy) in enumerate(cands):
        # enter placement mode: click NAPOWR icon (deduct 600, create limbo)
        ok_i, _ = click_client(pid, 2328, 480, "left")
        if not ok_i:
            continue
        time.sleep(0.3)
        credit_after_icon = m.u32(ph + CREDIT_OFF)
        limbo = [s for s in napowr_state(m, ph) if s["o1"] == 1]
        if not limbo:
            # icon click did not create limbo -> maybe still in placement; try hover anyway
            pass
        # hover candidate, inspect cursor
        move_client(pid, cx, cy)
        time.sleep(0.35)
        force_foreground(game_hwnd(pid))
        time.sleep(0.15)
        img = ImageGrab.grab(all_screens=False)
        red, green = cursor_colors(img, cx, cy)
        # valid if green outline present and red X absent
        valid = (green >= 25 and red < 120)
        results.append({"attempt": attempt, "xy": [cx, cy], "red": red, "green": green,
                        "valid_guess": valid, "credit_after_icon": credit_after_icon,
                        "limbo": limbo})
        if valid:
            # click to place, same foreground session
            u32 = ctypes.windll.user32
            if u32.GetForegroundWindow() != game_hwnd(pid):
                force_foreground(game_hwnd(pid)); time.sleep(0.2)
            img.save(os.path.join(EVID, "fp_valid_ghost_%d.png" % attempt))
            u32.mouse_event(0x0002, 0, 0, 0, 0); time.sleep(0.12)
            u32.mouse_event(0x0004, 0, 0, 0, 0)
            time.sleep(1.2)
            credit_after = m.u32(ph + CREDIT_OFF)
            ns = napowr_state(m, ph)
            placed = [s for s in ns if s["o1"] == 0 and s["o2"] == 1 and s["valid"]]
            results[-1].update({"credit_after": credit_after, "napowr_after": ns,
                                "placed": placed, "clicked": True})
            img2 = ImageGrab.grab(all_screens=False)
            img2.resize((1600, 900)).save(os.path.join(EVID, "fp_clicked_%d.png" % attempt))
            if placed:
                rec["SUCCESS"] = results[-1]
                break
        # cancel current placement (right click) to reset before next attempt
        click_client(pid, cx, cy, "right")
        time.sleep(0.2)
    rec["results"] = results
    with open(os.path.join(EVID, "final_place.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps({"success": "SUCCESS" in rec,
                      "results": [(r["xy"], r["red"], r["green"], r.get("clicked", False)) for r in results]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
