#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177 最终只读快照：G0/G1/G2 + 全部 BuildingClass 的 O1/O2/O3/O4/O5/O6 + 格链遍历尝试。
输出 JSON 行到 stdout（调用方重定向到 EVIDENCE）。全部 ReadProcessMemory。
"""
import argparse
import json
import sys
import time

import w177_core as W


def snap_one(m, tag):
    rec = {"tag": tag, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "G": W.globals_snapshot(m)}
    items, count, bl = W.list_buildings(m)
    rec["bldg_array"] = {"items": items, "count": count}
    # 也按 vftable 扫 AbstractClass::Array（BuildingClass vt=0x7E3EBC）
    avt = m.u32(0x00B0F720)
    aitems = m.u32(0x00B0F724)
    acount = m.u32(0x00B0F730)
    bldgs = []
    if aitems and acount and 0 < acount < 20000:
        for i in range(acount):
            p = m.u32(aitems + 4 * i)
            if not p:
                continue
            if m.u32(p) == 0x007E3EBC:
                o1 = m.u8(p + W.OFF_O1)
                o2 = m.u8(p + W.OFF_O2)
                o3 = m.u8(p + W.OFF_O3)
                nxt = m.u32(p + W.OFF_NEXT)
                typ = m.u32(p + W.OFF_MAP)
                # 尝试读 type 名字（BuildingTypeClass 名通常在 type+0x24? 只记录类型指针）
                bldgs.append({"idx": i, "obj": hex(p), "o1_81": o1, "o2_74": o2,
                              "o3_80": o3, "o5_next30": hex(nxt or 0),
                              "type520": hex(typ or 0)})
    rec["buildings"] = bldgs
    rec["building_count"] = len(bldgs)
    # O1 分布
    rec["o1_hist"] = {}
    for b in bldgs:
        k = str(b["o1_81"])
        rec["o1_hist"][k] = rec["o1_hist"].get(k, 0) + 1
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, default=None)
    ap.add_argument("--samples", type=int, default=5)
    ap.add_argument("--interval", type=float, default=1.0)
    a = ap.parse_args()
    pid = a.pid or W.pid_of()
    if not pid:
        print("gamemd not running")
        return 2
    m = W.Mem(pid)
    for i in range(a.samples):
        print(json.dumps(snap_one(m, "final_%02d" % i)))
        if i + 1 < a.samples:
            time.sleep(a.interval)
    return 0


if __name__ == "__main__":
    sys.exit(main())
