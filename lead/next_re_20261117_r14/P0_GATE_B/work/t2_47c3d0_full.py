#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T2: enumerate all direct E8 calls to 0x47C3D0 + full disasm of 0x47C3D0."""
import sys, struct
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_GATE_B\work')
import peutil
from peutil import *

def is_data(i): return i.id==0 or i.mnemonic.startswith('.')

# --- enumerate call sites of 0x47C3D0 ---
TGT=0x47C3D0
tb=read(0x401000, 0x7E1000-0x401000)
sites=[]
for i in range(len(tb)-5):
    if tb[i]==0xE8:
        rel=struct.unpack_from('<i',tb,i+1)[0]
        a=0x401000+i
        if a+5+rel==TGT: sites.append(a)
print("direct E8 call sites of 0x47C3D0 = %d" % len(sites))
for a in sites: print("  0x%08X" % a)

# also any LE dword occurrence of 0x47C3D0 in whole image
pat=struct.pack('<I',TGT)
occ=[]
for sn,sva,vsz,pr,rs in peutil._SECTIONS:
    sec=read(sva,max(vsz,rs)); idx=0
    while True:
        j=sec.find(pat,idx)
        if j<0:break
        occ.append((sn,sva+j)); idx=j+1
print("LE dword occurrences of 0x47C3D0 pointer = %d" % len(occ))
for sn,va in occ: print("  [%s] 0x%08X" % (sn,va))

# --- full disasm of 0x47C3D0 to function end ---
BASE=0x47C3D0; END=0x47C700
insns=[i for i in disasm(BASE,END-BASE,skipdata=True)]
real=[i for i in insns if not is_data(i)]
last_ret=max([i.address for i in real if i.mnemonic.startswith('ret')] or [BASE])
print()
print("0x47C3D0 last ret within window = 0x%08X ; real insns=%d" % (last_ret,len(real)))
print("=== FULL 0x47C3D0 disasm ===")
for i in insns:
    if i.address>last_ret: break
    line=fmt_insn(i)
    if is_data(i):
        line+=" ; DATA"
    else:
        marks=[]
        if i.mnemonic.startswith('ret'): marks.append('RET')
        if i.mnemonic=='setg': marks.append('SETG')
        for op in i.operands:
            if op.type==X86_OP_MEM:
                if op.mem.base==X86_REG_ESP and op.mem.disp>=0x18: marks.append('ARG[esp+%X]'%op.mem.disp)
                if op.mem.disp in (0xE4,0xE8): marks.append('CELL+%X'%op.mem.disp)
        if marks: line+="  ; "+",".join(marks)
    print(line)

print()
print("=== summary inside 0x47C3D0 ===")
print("-- setg instructions --")
for i in real:
    if i.address<=last_ret and i.mnemonic=='setg': print("  %08X %s %s"%(i.address,i.mnemonic,i.op_str))
print("-- esp args --")
for i in real:
    if i.address<=last_ret:
        for op in i.operands:
            if op.type==X86_OP_MEM and op.mem.base==X86_REG_ESP and op.mem.disp>=0x18:
                print("  %08X %s %s"%(i.address,i.mnemonic,i.op_str))
print("-- cell +E4/+E8 reads --")
for i in real:
    if i.address<=last_ret:
        for op in i.operands:
            if op.type==X86_OP_MEM and op.mem.disp in (0xE4,0xE8):
                print("  %08X disp=%X %s %s"%(i.address,op.mem.disp,i.mnemonic,i.op_str))
print("-- WhatAmI vcall [..+0x2c] and cmp --")
for i in real:
    if i.address<=last_ret and i.mnemonic=='call' and i.operands and i.operands[0].type==X86_OP_MEM:
        if i.operands[0].mem.disp==0x2c: print("  VCALL %08X %s"%(i.address,fmt_insn(i).split(' ',2)[-1]))
    if i.address<=last_ret and i.mnemonic=='cmp' and i.operands and i.operands[-1].type==X86_OP_IMM:
        if i.operands[-1].imm in (1,2,6,15,0x24,0x0F): print("  CMP %08X %s %s"%(i.address,i.mnemonic,i.op_str))
