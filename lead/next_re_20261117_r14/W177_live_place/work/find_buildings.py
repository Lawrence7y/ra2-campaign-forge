#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 AbstractClass::Array 遍历所有对象，按 vftable 分类，找 BuildingClass(vt=0x7E3EBC)。
全部只读。输出 vftable 直方图 + 建筑对象列表（含 O1/O2/O3/O4/O6）。
"""
import argparse
import collections
import sys

import w177_core as W

A_ABSTRACT_VT = 0x00B0F720
BUILDING_VT = 0x007E3EBC


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, default=None)
    ap.add_argument("--show-all", action="store_true")
    a = ap.parse_args()
    pid = a.pid or W.pid_of()
    if not pid:
        print("gamemd not running")
        return 2
    m = W.Mem(pid)
    vt = m.u32(A_ABSTRACT_VT)
    items = m.u32(A_ABSTRACT_VT + 4)
    count = m.u32(A_ABSTRACT_VT + 0x10)
    print("abstract base=%08X vt=%08X items=%08X count=%d (G2@%08X=%s)" % (
        A_ABSTRACT_VT, vt or 0, items or 0, count or 0, W.A_ABSTRACT, m.u32(W.A_ABSTRACT)))
    hist = collections.Counter()
    buildings = []
    objs = []
    if items and count and 0 < count < 20000:
        for i in range(count):
            p = m.u32(items + 4 * i)
            if not p:
                continue
            v = m.u32(p)
            hist[v] += 1
            objs.append((i, p, v))
            if v == BUILDING_VT:
                buildings.append((i, p))
    print("walked %d nonnull objs; distinct vt=%d" % (len(objs), len(hist)))
    print("top vftables:")
    for v, c in hist.most_common(15):
        print("  %08X  %d" % (v or 0, c))
    print("BUILDING (vt=%08X) count=%d" % (BUILDING_VT, len(buildings)))
    for i, p in buildings:
        print("  idx=%d p=%08X o1(81)=%s o2(74)=%s o3(80)=%s owner(21C)=%s map(520)=%s next(30)=%s" % (
            i, p, m.u8(p + W.OFF_O1), m.u8(p + W.OFF_O2), m.u8(p + W.OFF_O3),
            hex(m.u32(p + W.OFF_OWNER) or 0), hex(m.u32(p + W.OFF_MAP) or 0),
            hex(m.u32(p + W.OFF_NEXT) or 0)))
    if a.show_all:
        print("all objects (first 80):")
        for i, p, v in objs[:80]:
            print("  %3d %08X vt=%08X o1=%s" % (i, p, v or 0, m.u8(p + W.OFF_O1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
