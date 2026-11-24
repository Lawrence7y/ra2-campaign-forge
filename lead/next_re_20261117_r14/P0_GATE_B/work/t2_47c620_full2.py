#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Full disassembly of 0x47C620 with skipdata-safe guards; find true function end.
Prints all instructions in 0x47C620..0x47CC00 with markers."""
import sys
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_GATE_B\work')
import peutil
from peutil import *

BASE = 0x47C620
END  = 0x47CC00
def is_data(i): return i.id==0 or i.mnemonic.startswith('.')
def targets_of(i):
    out=[]
    if is_data(i): return out
    if i.mnemonic in ('call','jmp','je','jne','ja','jae','jb','jbe','jg','jge','jl','jle','jo','jno','js','jns','jp','jnp'):
        for op in i.operands:
            if op.type==X86_OP_IMM: out.append(op.imm)
    return out

insns=[i for i in disasm(BASE, END-BASE, skipdata=True)]
# find last RET before run of int3/nop padding following the function
real=[i for i in insns if not is_data(i)]
last_ret=None
for i in real:
    if i.mnemonic.startswith('ret'): last_ret=i.address
print("last ret within window: 0x%08X" % last_ret)
print("total real insns: %d ; decoded slots: %d" % (len(real), len(insns)))

# Determine function end: from BASE, follow largest contiguous block of real insns
# (skipdata gaps mark data/padding). Print everything from BASE to last_ret.
print()
print("=== 0x47C620..last_ret (%08X) full ===" % last_ret)
for i in insns:
    if i.address > last_ret: break
    line = fmt_insn(i)
    if is_data(i):
        line += "  ; DATA"
    else:
        marks=[]
        if i.mnemonic.startswith('ret'): marks.append('RET')
        for op in i.operands:
            if op.type==X86_OP_MEM:
                if op.mem.base==X86_REG_ESP and op.mem.disp>=0x18: marks.append('ARG[esp+%X]'%op.mem.disp)
                if op.mem.disp in (0xE4,0xE8): marks.append('CELL+%X'%op.mem.disp)
        if marks: line += "   ; " + ",".join(marks)
    print(line)
