#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用只读快照：G0/G1/G2 + BuildingClass::Array 概况 + 可选 building 详情。"""
import argparse
import json
import os
import sys
import time

import w177_core as W


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, default=None)
    ap.add_argument("--list", action="store_true", help="列出 BuildingClass::Array 全部对象")
    ap.add_argument("--secs", type=float, default=0.0, help=">0 时按间隔连续采样")
    ap.add_argument("--interval", type=float, default=0.5)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    pid = a.pid or W.pid_of()
    if not pid:
        print("gamemd not running")
        return 2
    m = W.Mem(pid)
    rows = []
    t0 = time.perf_counter()
    n = 0
    while True:
        g = W.globals_snapshot(m)
        items, count = W.building_array(m)
        rec = {"t": round(time.perf_counter() - t0, 3), **g,
               "bldg_items": items, "bldg_count": count}
        if a.list:
            _, _, bl = W.list_buildings(m)
            rec["buildings"] = [{"i": i, "p": hex(p),
                                 "o1": m.u8(p + W.OFF_O1),
                                 "o2": m.u8(p + W.OFF_O2),
                                 "o3": m.u8(p + W.OFF_O3),
                                 "owner": m.u32(p + W.OFF_OWNER),
                                 "map": m.u32(p + W.OFF_MAP)} for i, p in bl]
        rows.append(rec)
        print(json.dumps(rec))
        n += 1
        if a.secs <= 0 or time.perf_counter() - t0 >= a.secs:
            break
        time.sleep(a.interval)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        print("saved %d rows -> %s" % (n, a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
