#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify the rejection chain and RTTI (fail-closed)."""
import sys
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_GATE_B\work')
import peutil
from peutil import *
def is_data(i): return i.id==0 or i.mnemonic.startswith('.')

print("=== 0x449440 full (BuildingClass vtable slot +0x1AC) ===")
for i in disasm(0x449440,0x80,skipdata=True):
    if is_data(i): continue
    print("  "+fmt_insn(i))
    if i.mnemonic.startswith('ret'): break

print("\n=== RTTI for BuildingClass vtable 0x7E3EBC (fail-closed) ===")
VT=0x7E3EBC
col=u32(VT-4); print("COL=0x%08X"%col)
if col and 0x812000<=col<0xB79BE4:
    td=u32(col+0xc); print("COL+0xC -> TD=0x%08X"%td)
    if td and 0x812000<=td<0xB79BE4:
        nm=read(td+8,40)  # MSVC TypeDescriptor::name is inline char[], not a pointer
        print("TD+8 inline name bytes: %r"%nm)
    else:
        print("TD invalid -> name='?' fail-closed")
else:
    print("COL invalid -> fail-closed")

print("\n=== no WhatAmI 15/1 compare in placement funcs (0x43F180,0x449440,0x47C620) ===")
for base,size,name in [(0x43F180,2443,'0x43F180'),(0x449440,117,'0x449440'),(0x47C620,0xA60,'0x47C620')]:
    vals=[]
    for i in disasm(base,size,skipdata=True):
        if is_data(i): continue
        if i.mnemonic=='cmp' and i.operands and i.operands[-1].type==X86_OP_IMM:
            v=i.operands[-1].imm & 0xffffffff
            if v in (1,15,0xF): vals.append((i.address,v,i.op_str))
    print("  %s : cmp-15/1 count=%d %s"%(name,len(vals),vals[:10]))
