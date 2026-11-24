#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单步合成输入（用已校验的 w177_click.click_client）+ 截图 + 全局读数。
所有输入经 click_client（前台+归属校验），绝不裸 SetCursorPos。"""
import argparse
import json
import os
import sys
import time

import w177_core as W
import wb_probe as P
from w177_click import click_client, game_hwnd, force_foreground
import shot

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cx", type=int, default=None)
    ap.add_argument("--cy", type=int, default=None)
    ap.add_argument("--button", choices=["left", "right"], default="left")
    ap.add_argument("--key", default=None, help="VK decimal or 0x..; tap after click")
    ap.add_argument("--prefocus", action="store_true")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--wait", type=float, default=1.0)
    ap.add_argument("--bbox", default="0,0,800,600")
    a = ap.parse_args()
    pid = W.pid_of()
    if not pid:
        print("no gamemd")
        return 2
    rec = {"pid": pid, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "tag": a.tag}
    hwnd = game_hwnd(pid)
    rec["hwnd"] = hex(hwnd) if hwnd else None
    if a.prefocus and hwnd:
        rec["prefocus_ok"] = force_foreground(hwnd)
    if a.cx is not None and a.cy is not None:
        ok, info = click_client(pid, a.cx, a.cy, a.button)
        rec["click_ok"] = ok
        rec["click_info"] = info
        print("click ok=%s %s" % (ok, info))
        if not ok:
            print(json.dumps(rec))
            return 3
    if a.key:
        # 用合成键盘（不写进程内存）；依赖前台
        import ctypes
        u32 = ctypes.windll.user32
        vk = int(a.key, 0)
        u32.keybd_event(vk & 0xFF, 0, 0, 0)
        time.sleep(0.06)
        u32.keybd_event(vk & 0xFF, 0, 2, 0)
        rec["key"] = hex(vk)
        print("key %s" % a.key)
    time.sleep(a.wait)
    bbox = tuple(int(x) for x in a.bbox.split(",")) if a.bbox else None
    path, size, frac = shot.save(a.tag, bbox=bbox)
    rec["shot"] = os.path.basename(path)
    rec["shot_size"] = size
    rec["nonblack_frac"] = round(frac, 4)
    m = W.Mem(pid)
    rec["globals"] = P.globals_snapshot(m)
    items, count = W.building_array(m)
    rec["bldg_array"] = {"items": items, "count": count}
    hitems, hcount, houses = P.house_array(m)
    rec["houses"] = {"items": hitems, "count": hcount, "n": len(houses)}
    print(json.dumps(rec, ensure_ascii=False))
    with open(os.path.join(os.path.dirname(HERE), "EVIDENCE", a.tag + ".json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
