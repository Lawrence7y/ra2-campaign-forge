#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T4: full disassembly of 0x43F180 (BuildingClass slot73 Unlimbo) with check/failure map."""
import sys
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_GATE_B\work')
import peutil
from peutil import *
def is_data(i): return i.id==0 or i.mnemonic.startswith('.')

BASE=0x43F180; SIZE=2443
insns=[i for i in disasm(BASE,SIZE,skipdata=True)]
print("0x43F180 full disassembly (%d real insns, %d bytes):"%(len([i for i in insns if not is_data(i)]),SIZE))
for i in insns:
    if is_data(i): continue
    m=""
    if i.mnemonic in ('call','jmp') and i.operands and i.operands[0].type==X86_OP_IMM:
        m=" ; -> 0x%08X"%i.operands[0].imm
    print("  "+fmt_insn(i)+m)
