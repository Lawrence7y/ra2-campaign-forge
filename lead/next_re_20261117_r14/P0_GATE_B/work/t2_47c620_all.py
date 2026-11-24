#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Full disassembly of 0x47C620 across fixed byte range until function end.
Identify all returns, all [esp+N], all WhatAmI comparisons, all +0xE4/+0xE8 reads."""
import sys
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_GATE_B\work')
import peutil
from peutil import *

BASE = 0x47C620
END  = 0x47C900   # generous; function ~640B ends ~0x47C8A0
def is_data(i): return i.id==0 or i.mnemonic.startswith('.')

insns = []
for insn in disasm(BASE, END-BASE, skipdata=True):
    insns.append(insn)

# Print all, but mark returns / esp refs / WhatAmI cmp / e4/e8 reads
print("=== FULL 0x47C620 (%d insns decoded 0x%08X..0x%08X) ===" % (len(insns), BASE, END))
for insn in insns:
    line = fmt_insn(insn)
    marks=[]
    if insn.mnemonic.startswith('ret'): marks.append('RET')
    for op in insn.operands:
        if op.type==X86_OP_MEM:
            if op.mem.base==X86_REG_ESP: marks.append('ESP%d'%op.mem.disp)
            if op.mem.disp in (0xE4,0xE8): marks.append('OFF+%X'%op.mem.disp)
    if marks: line += "   ; " + ",".join(marks)
    print(line)

print()
print("=== returns ===")
for i in insns:
    if i.mnemonic.startswith('ret'):
        print("  %08X %s %s" % (i.address,i.mnemonic,i.op_str))
print("=== [esp+N] refs (post-prologue; arg mapping: [esp+0x1c]=arg1,[esp+0x20]=arg2,[esp+0x24]=arg3) ===")
for i in insns:
    if is_data(i): continue
    for op in i.operands:
        if op.type==X86_OP_MEM and op.mem.base==X86_REG_ESP:
            print("  %08X %s %s" % (i.address,i.mnemonic,i.op_str))
print("=== WhatAmI comparisons (cmp reg,imm after vcall [vptr+0x2c]) ===")
for k,i in enumerate(insns):
    if is_data(i): continue
    if i.mnemonic=='cmp' and i.operands and i.operands[-1].type==X86_OP_IMM:
        v=i.operands[-1].imm
        if v in (6,2,0x24,15,1) or v==0x0F:
            print("  %08X %s %s" % (i.address,i.mnemonic,i.op_str))
print("=== +0xE4 / +0xE8 reads ===")
for i in insns:
    if is_data(i): continue
    for op in i.operands:
        if op.type==X86_OP_MEM and op.mem.disp in (0xE4,0xE8):
            print("  %08X disp=+%X  %s %s" % (i.address,op.mem.disp,i.mnemonic,i.op_str))
