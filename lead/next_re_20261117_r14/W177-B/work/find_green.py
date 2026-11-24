#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在放置模式已激活时，密集扫hover点找绿色合法格。找到则报告其屏幕坐标。"""
import json
import os
import time
import ctypes
from PIL import ImageGrab
import sys
import w177_core as W
from w177_click import move_client
from auto_place import detect_green, detect_red

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass


def main():
    pid = W.pid_of()
    if not pid:
        print("no gamemd"); return 2
    found = None
    log = []
    # dense grid over revealed map area (physical coords)
    for y in range(300, 1251, 120):
        for x in range(200, 2001, 160):
            move_client(pid, x, y)
            time.sleep(0.10)
            img = ImageGrab.grab(all_screens=False)
            g = detect_green(img)
            r = detect_red(img)
            log.append({"xy": [x, y], "g": g, "r": r})
            if g:
                found = {"hover": [x, y], "g": g, "r": r}
                break
        if found:
            break
    with open(os.path.join(EVID, "find_green.json"), "w", encoding="utf-8") as f:
        json.dump({"found": found, "log": log}, f, ensure_ascii=False, indent=2)
    if found:
        print("FOUND", json.dumps(found))
        ImageGrab.grab(all_screens=False).resize((1600, 900)).save(os.path.join(EVID, "find_green.png"))
    else:
        print("NOT FOUND %d probes; sample:" % len(log), log[:3])
    return 0


if __name__ == "__main__":
    main()
