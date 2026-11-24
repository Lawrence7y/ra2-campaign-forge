#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fully disassemble the 20 push-imm32 first candidates to decide if real functions."""
import sys, os, struct
sys.stdout.reconfigure(encoding="utf-8")
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from res2_common import *
pe=PE(); sw=Sweep(pe); at=Atlas()
addrs=[0x40A210,0x40A780,0x40A790,0x40D200,0x47A7D0,0x4E8060,0x4E80A0,
       0x5355C0,0x5B81B0,0x5E8720,0x611E50,0x63A210,0x68E890,0x72CCB0,
       0x7773C0,0x7786E0,0x78D800,0x799910,0x7B0090,0x7B00D0]
for a in addrs:
    d=pe.try_read(a,64)
    print("\n==== %08X ==== pred=%s bytes=%s"%(a,sw.endmap.get(a),d[:16].hex()))
    for ins in md32(True).disasm(d,a):
        print("   %08X: %-8s %s"%(ins.address, ins.mnemonic, ins.op_str))
        if ins.address-a>48: break
