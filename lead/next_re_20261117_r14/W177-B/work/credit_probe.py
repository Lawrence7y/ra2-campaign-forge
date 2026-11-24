#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同时抓 credit 显示区截图 + PlayerHouse 全 dword dump，用于定位 credits 字段偏移。
截图→读内存 在几百毫秒内完成，误差仅来自收入轮询。"""
import json
import os
import struct
import sys
import time

import ctypes
from PIL import ImageGrab

import w177_core as W
import wb_probe as P

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

# credit display in full screenshot (1600x900 scaled from 2560x1440) is at x~1460-1560,y~0-30 scaled
# physical: x = 1460/0.625=2336 .. 1560/0.625=2496, y=0..48
CREDIT_BBOX = (2300, 0, 2520, 60)


def main():
    pid = W.pid_of()
    if not pid:
        print("no gamemd"); return 2
    m = W.Mem(pid)
    ph = P.player_house(m)
    # 同时：先截图，再读内存
    img = ImageGrab.grab(bbox=CREDIT_BBOX, all_screens=False)
    img.resize((880, 240)).save(os.path.join(EVID, "credit_probe.png"))
    ts = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    frame = m.u32(W.A_FRAME)
    n = 0x160C0
    buf = P.read_bytes(m, ph, n)
    dump = []
    if buf:
        for off in range(0, n - 3, 4):
            v = struct.unpack_from("<I", buf, off)[0]
            if v != 0:
                dump.append([hex(off), v])
    rec = {"ts": ts, "frame": frame, "ph": hex(ph), "dump": dump}
    with open(os.path.join(EVID, "credit_probe.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f)
    # 打印 credit-like 值（1000..1000000）
    print("ts=%s frame=%d ph=%s nonzero=%d" % (ts, frame, hex(ph), len(dump)))
    print("credit-like dwords (1000..2000000):")
    for offh, v in dump:
        if 1000 <= v <= 2000000:
            print("  %s = %d" % (offh, v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
