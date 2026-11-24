#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统计当前 BuildingClass 里 YAPOWR / YACNST 等类型的数量与全部建筑 O1 快照。stdout JSON。"""
import json
import sys
import w177_core as W


def scan(pid):
    m = W.Mem(pid)
    avt = m.u32(0x00B0F720)
    aitems = m.u32(0x00B0F724)
    acount = m.u32(0x00B0F730)
    res = {"frame": m.u32(W.A_FRAME), "mode": m.u32(W.A_MODE),
           "objects": m.u32(W.A_ABSTRACT), "buildings": [], "types": {}}
    if aitems and acount and 0 < acount < 20000:
        for i in range(acount):
            p = m.u32(aitems + 4 * i)
            if not p or m.u32(p) != 0x007E3EBC:
                continue
            typ = m.u32(p + W.OFF_MAP)  # +0x520 = BuildingTypeClass
            sid = ""
            if typ:
                raw = b""
                for j in range(8):
                    v = m.u8(typ + 0x24 + j)
                    if v is None or v == 0 or v < 0x20 or v > 0x7e:
                        break
                    raw += bytes([v])
                sid = raw.decode("latin-1")
            res["types"][sid] = res["types"].get(sid, 0) + 1
            res["buildings"].append({"idx": i, "obj": hex(p), "type": sid,
                                     "o1": m.u8(p + W.OFF_O1), "o2": m.u8(p + W.OFF_O2),
                                     "o3": m.u8(p + W.OFF_O3), "next": hex(m.u32(p + W.OFF_NEXT) or 0)})
    return res


if __name__ == "__main__":
    pid = W.pid_of()
    if not pid:
        print("{}")
        sys.exit(2)
    print(json.dumps(scan(pid)))
