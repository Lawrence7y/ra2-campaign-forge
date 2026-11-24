#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""暴力定位可进入放置模式的建造图标坐标：对每个候选图标坐标 click_client，
然后把鼠标移到已知开阔地，检测绿色 ghost。找到即停并报告。"""
import json
import os
import time
import ctypes
from PIL import ImageGrab

import w177_core as W
from w177_click import click_client, move_client
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
    # hover point: pick several clearly-revealed open spots from recent screenshot
    hovers = [(900, 700), (1000, 800), (800, 600), (1100, 700)]
    # candidate build-icon centers (physical): buildings tab rows 1-3, both columns
    cands = []
    for y in (470, 490, 510, 570, 590):
        for x in (2300, 2320, 2340, 2380, 2400, 2420):
            cands.append((x, y))
    found = None
    log = []
    for (ix, iy) in cands:
        ok, info = click_client(pid, ix, iy, "left")
        if not ok:
            continue
        time.sleep(0.18)
        for (hx, hy) in hovers:
            move_client(pid, hx, hy)
            time.sleep(0.20)
            img = ImageGrab.grab(all_screens=False)
            g = detect_green(img)
            r = detect_red(img)
            log.append({"icon": [ix, iy], "hover": [hx, hy], "g": g, "r": r})
            if g:
                found = {"icon": [ix, iy], "hover": [hx, hy], "g": g, "r": r}
                break
        if found:
            break
    with open(os.path.join(EVID, "find_icon.json"), "w", encoding="utf-8") as f:
        json.dump({"found": found, "log": log}, f, ensure_ascii=False, indent=2)
    if found:
        print("FOUND", json.dumps(found))
        ImageGrab.grab(all_screens=False).resize((1600, 900)).save(os.path.join(EVID, "find_icon_green.png"))
    else:
        print("NOT FOUND; %d probes" % len(log))
    return 0


if __name__ == "__main__":
    main()
