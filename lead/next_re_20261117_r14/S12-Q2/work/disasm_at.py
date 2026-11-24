#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Disassemble a window of cached instructions around a given address."""
import sys
from core_disasm import get_insns
D = get_insns()
INS = D["insns"]
# binary search by address
addrs = [x[0] for x in INS]
import bisect

def dump_around(addr, before=40, after=40):
    i = bisect.bisect_left(addrs, addr)
    lo = max(0, i-before)
    hi = min(len(INS), i+after)
    for (a,s,m,o) in INS[lo:hi]:
        mark = ">>>" if a==addr else "   "
        print("%s %08X  %-8s %s" % (mark,a,m,o))

if __name__ == "__main__":
    addr = int(sys.argv[1],16)
    before = int(sys.argv[2]) if len(sys.argv)>2 else 40
    after = int(sys.argv[3]) if len(sys.argv)>3 else 40
    dump_around(addr,before,after)
