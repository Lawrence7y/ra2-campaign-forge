#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用只读内存读取：dump 一组地址/区间。addr 支持 0x 十六进制。"""
import argparse
import sys

import w177_core as W


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, default=None)
    ap.add_argument("addrs", nargs="*", help="单地址列表，读 u32")
    ap.add_argument("--range", nargs=2, metavar=("LO", "HI"), help="读连续 dword 区间")
    ap.add_argument("--ptr", action="store_true")
    a = ap.parse_args()
    pid = a.pid or W.pid_of()
    if not pid:
        print("gamemd not running")
        return 2
    m = W.Mem(pid)
    addrs = []
    if a.range:
        lo, hi = int(a.range[0], 0), int(a.range[1], 0)
        addrs = list(range(lo, hi, 4))
    else:
        addrs = [int(x, 0) for x in a.addrs]
    for va in addrs:
        v = m.u32(va)
        extra = ""
        if a.ptr and v:
            v2 = m.u32(v)
            extra = " -> [ptr]=%s(0x%X)" % (v2, v2 or 0)
        print("0x%08X = %-12s 0x%08X%s" % (va, v, v or 0, extra))
    return 0


if __name__ == "__main__":
    sys.exit(main())
