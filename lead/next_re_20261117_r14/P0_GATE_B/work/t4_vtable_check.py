#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify: BuildingClass vtable slots used in 0x43F180, and globals."""
import sys
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_GATE_B\work')
import peutil
from peutil import *

# BuildingClass main vtable 0x7E3EBC (from R14_COMMON §2). Read slots.
VT=0x7E3EBC
for off in (0x1ac,0x1b4,0x1b8,0x8c,0xd8,0x2c,0x3c,0x48,0x280,0xf8,0x1e4,0x1bc,0x464,0x160,0x68,0x6c,0xac,0x160):
    val=u32(VT+off)
    sec=section_of(val)
    print("vtable 0x%08X +0x%X = 0x%08X  [%s]"%(VT,off,val,sec[0] if sec else '?'))

# Also check RTTI name for the vtable
col=u32(VT-4)
print("\nvtable[-1] COL = 0x%08X"%col)
td=u32(col+0xC)
print("COL+0xC -> TD = 0x%08X"%td)
if td:
    nameaddr=u32(td+8)
    print("TD+8 name ptr = 0x%08X -> %r"%(nameaddr,read(nameaddr,40)))

# globals used as gates
for g in (0xa8e7ac,0xa8e9a0,0xa8ed6b,0xa83d4c,0xa8ec1c,0x880990,0x880968):
    print("global 0x%08X "@g)
