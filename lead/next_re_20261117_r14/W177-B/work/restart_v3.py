#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""干净重开 v3：进局->精确部署MCV->确认NACNST->随后由调用者继续放置。输入全经 click_client。"""
import os
import subprocess
import sys
import time

import w177_core as W
import wb_probe as P
from w177_click import click_client
from PIL import ImageGrab

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")


def ps(cmd):
    return subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                          capture_output=True, text=True).stdout.strip()


def shot(tag):
    ImageGrab.grab(all_screens=False).resize((1600, 900)).save(os.path.join(EVID, tag + ".png"))


def main():
    mypid = open(os.path.join(HERE, "game.pid")).read().strip()
    ps("Stop-Process -Id %s -Force -ErrorAction SilentlyContinue" % mypid)
    time.sleep(2)
    assert ps("@(Get-Process gamemd -ErrorAction SilentlyContinue).Count") == "0", "residual"
    subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "launch.py")],
                   capture_output=True, text=True)
    time.sleep(4)
    pid = W.pid_of()
    print("pid", pid)
    # menu: single player -> skirmish
    click_client(pid, 720, 220); time.sleep(1.0)
    shot("v3_single")
    click_client(pid, 720, 305); time.sleep(1.5)
    shot("v3_skirmish")
    # country dropdown open by default -> select Libya at (310,235)
    click_client(pid, 310, 235); time.sleep(0.6)
    shot("v3_libya")
    # start game
    click_client(pid, 720, 262); time.sleep(6.0)
    m = W.Mem(pid)
    g = W.globals_snapshot(m)
    print("after start", g)
    if not g["objects"]:
        shot("v3_notingame"); return 3
    time.sleep(2)
    shot("v3_ingame")
    m = W.Mem(pid); ph = P.player_house(m)
    print("ph", hex(ph), "credit", m.u32(ph + 0x30C))
    return 0


if __name__ == "__main__":
    sys.exit(main())
