#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Blitz: restart -> skirmish -> deploy MCV -> immediately place several NAPOWRs.
Full evidence per placement. All clicks via w177_click (foreground+owner verify)."""
import json
import os
import subprocess
import sys
import time
import ctypes
from PIL import ImageGrab

import w177_core as W
import wb_probe as P
from w177_click import click_client, move_client, force_foreground, game_hwnd
from final_place import cursor_colors

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")
CREDIT_OFF = 0x30C
ctypes.windll.user32.SetProcessDPIAware()


def ps(cmd):
    return subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                          capture_output=True, text=True).stdout.strip()


def snap_bld(m, ph):
    return [P.one_building(m, i, o) for i, o in P.enumerate_buildings(m)[2]
            if P.one_building(m, i, o)["owner_21C"] == ph]


def napowr(m, ph):
    out = []
    for i, o in P.enumerate_buildings(m)[2]:
        b = P.one_building(m, i, o)
        if b["owner_21C"] == ph and b["type"] == "NAPOWR":
            c = b["cell"]
            out.append({"obj": b["obj_hex"], "o1": b["o1_81"], "o2": b["o2_74"],
                        "cx": c["cellX"], "cy": c["cellY"], "valid": c["valid"],
                        "cell": hex(c["cell"]) if c.get("cell") else None,
                        "chainA": b["chains"]["lenA"], "chainB": b["chains"]["lenB"],
                        "nodesA": b["chains"]["nodesA"], "owner": b["owner_hex"]})
    return out


def main():
    # restart
    try:
        mypid = open(os.path.join(HERE, "game.pid")).read().strip()
        ps("Stop-Process -Id %s -Force -ErrorAction SilentlyContinue" % mypid)
    except Exception:
        pass
    time.sleep(1.5)
    subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "launch.py")],
                   capture_output=True, text=True)
    time.sleep(4)
    pid = W.pid_of()
    # menu
    click_client(pid, 720, 220); time.sleep(0.8)
    click_client(pid, 720, 305); time.sleep(1.2)
    click_client(pid, 310, 235); time.sleep(0.4)  # pick libya, close dropdown
    click_client(pid, 720, 262); time.sleep(5.0)
    m = W.Mem(pid)
    if not m.u32(W.A_FRAME):
        time.sleep(3); m = W.Mem(pid)
    ph = P.player_house(m)
    print("ingame frame", m.u32(W.A_FRAME), "ph", hex(ph), "credit", m.u32(ph + CREDIT_OFF))
    # deploy MCV: select at (1627,581), press D
    click_client(pid, 1627, 581); time.sleep(0.3)
    u32 = ctypes.windll.user32
    u32.keybd_event(0x44, 0, 0, 0); time.sleep(0.08); u32.keybd_event(0x44, 0, 2, 0)
    time.sleep(1.5)
    cony = [b for b in snap_bld(m, ph) if b["type"] == "NACNST"]
    print("conyards", [(b["obj_hex"], b["cell"]["cellX"], b["cell"]["cellY"]) for b in cony])
    ImageGrab.grab(all_screens=False).resize((1600, 900)).save(os.path.join(EVID, "blitz_deployed.png"))

    results = []
    # grid of candidate cells (physical) - try many, quick
    cands = [(1900,500),(1950,450),(1850,450),(2000,500),(1750,500),(2050,450),
             (1950,550),(1850,550),(2100,500),(1700,550),(1900,600),(2000,600),
             (1800,650),(2100,600),(1600,500),(2200,550)]
    for attempt, (cx, cy) in enumerate(cands):
        before_credit = m.u32(ph + CREDIT_OFF)
        before_nap = napowr(m, ph)
        # enter placement mode (icon); verify limbo + credit drop
        click_client(pid, 2328, 480); time.sleep(0.25)
        credit_icon = m.u32(ph + CREDIT_OFF)
        limbo = [s for s in napowr(m, ph) if s["o1"] == 1]
        entered = (credit_icon == before_credit - 600) or bool(limbo)
        if not entered:
            # maybe already in placement from prior; still try hover
            pass
        move_client(pid, cx, cy); time.sleep(0.28)
        force_foreground(game_hwnd(pid)); time.sleep(0.12)
        img = ImageGrab.grab(all_screens=False)
        red, green = cursor_colors(img, cx, cy)
        r = {"attempt": attempt, "xy": [cx, cy], "before_credit": before_credit,
             "credit_icon": credit_icon, "entered": entered, "limbo": limbo,
             "red": red, "green": green}
        # valid = no red-X and clear green outline
        if green >= 40 and red < 80 and entered:
            img.save(os.path.join(EVID, "blitz_ghost_%d.png" % attempt))
            u32.mouse_event(0x0002, 0, 0, 0, 0); time.sleep(0.12)
            u32.mouse_event(0x0004, 0, 0, 0, 0)
            time.sleep(1.0)
            after_credit = m.u32(ph + CREDIT_OFF)
            after_nap = napowr(m, ph)
            placed = [s for s in after_nap if s["o1"] == 0 and s["o2"] == 1 and s["valid"]]
            newplaced = [s for s in placed if s["obj"] not in {x["obj"] for x in before_nap}]
            r.update({"clicked": True, "after_credit": after_credit,
                      "after_nap": after_nap, "newplaced": newplaced})
            ImageGrab.grab(all_screens=False).resize((1600, 900)).save(
                os.path.join(EVID, "blitz_after_%d.png" % attempt))
            if newplaced:
                results.append(r)
                break
        else:
            # cancel placement to avoid stuck limbo
            click_client(pid, cx, cy, "right"); time.sleep(0.15)
        results.append(r)
    out = {"ph": hex(ph), "results": results,
           "success_count": sum(1 for r in results if r.get("newplaced"))}
    with open(os.path.join(EVID, "blitz.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps({"success_count": out["success_count"],
                      "rows": [(r["xy"], r["credit_icon"], r["red"], r["green"], r.get("entered")) for r in results]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
