#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Examine contiguous FPU-candidate region in full context: are they real functions or data?"""
import sys, os, struct
sys.stdout.reconfigure(encoding="utf-8")
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from res2_common import *
pe=PE(); sw=Sweep(pe); at=Atlas()
for start,end in [(0x403C80,0x403E20),(0x406880,0x406A00)]:
    print("\n===== REGION %08X..%08X ====="%(start,end))
    d=pe.try_read(start,end-start)
    for ins in md32(True).disasm(d,start):
        mark=""
        if ins.address%16==0: mark+=" [A16]"
        if sw.endmap.get(ins.address) in TERM: mark+=" [PRED-TERM]"
        print("  %08X: %-8s %-28s%s"%(ins.address, ins.mnemonic, ins.op_str, mark))
