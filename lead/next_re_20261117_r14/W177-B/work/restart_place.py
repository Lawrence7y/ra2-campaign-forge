#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""干净重开 + 立即尝试 NAPOWR 放置。全部输入经 click_client/wb_click（前台+归属校验）。"""
import os
import subprocess
import sys
import time

import w177_core as W
from w177_click import click_client, move_client
from wb_click import click_stable
from auto_place import detect_green, detect_red
from PIL import ImageGrab

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")


def ps(cmd):
    return subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                          capture_output=True, text=True).stdout.strip()


def main():
    # 1) close only my game
    mypid = open(os.path.join(HERE, "game.pid")).read().strip()
    ps("Stop-Process -Id %s -Force -ErrorAction SilentlyContinue" % mypid)
    time.sleep(2)
    cnt = ps("@(Get-Process gamemd -ErrorAction SilentlyContinue).Count")
    print("after close count=%s" % cnt)
    if cnt != "0":
        print("ABORT residual"); return 2
    # 2) relaunch
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "launch.py")],
                       capture_output=True, text=True)
    print(r.stdout)
    time.sleep(3)
    pid = W.pid_of()
    print("pid", pid)
    # 3) menu flow (building tab default likely)
    for tag, x, y, w in [("r_menu_single", 720, 220, 1.0),
                         ("r_menu_skirmish", 720, 305, 1.0),
                         ("r_setup_start", 720, 262, 5.0)]:
        ok, info = click_client(pid, x, y, "left")
        print(tag, ok)
        time.sleep(w)
    m = W.Mem(pid)
    print("globals", W.globals_snapshot(m))
    if not W.globals_snapshot(m)["objects"]:
        print("NOT IN GAME"); return 3
    # 4) capture sidebar to find NAPOWR icon
    ImageGrab.grab(all_screens=False).crop((2240, 250, 2560, 950)).save(os.path.join(EVID, "restart_sidebar.png"))
    # ensure buildings tab (house icon)
    click_stable(pid, 2310, 395); time.sleep(0.4)
    # 5) click NAPOWR icon ONCE (row1 left). default coords from tooltip
    ok, info = click_stable(pid, 2327, 487); print("napo icon", ok, info)
    time.sleep(0.35)
    # 6) hover dense grid find green
    found = None
    for y in range(400, 1101, 110):
        for x in range(300, 1901, 140):
            move_client(pid, x, y); time.sleep(0.08)
            img = ImageGrab.grab(all_screens=False)
            g = detect_green(img); r = detect_red(img)
            if g:
                found = (x, y, g, r); break
        if found: break
    print("found", found)
    if found:
        img.resize((1600, 900)).save(os.path.join(EVID, "restart_green.png"))
        gx, gy = found[2][0], found[2][1]
        ok, info = click_stable(pid, gx, gy); print("PLACE click", ok, info)
        time.sleep(1.0)
        img = ImageGrab.grab(all_screens=False)
        img.resize((1600, 900)).save(os.path.join(EVID, "restart_after.png"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
