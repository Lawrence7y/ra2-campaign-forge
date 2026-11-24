#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T4 check map: enumerate test/cmp -> immediate jcc in 0x43F180 mode1/3 path."""
import sys
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_GATE_B\work')
import peutil
from peutil import *
from capstone.x86 import *
def is_data(i): return i.id==0 or i.mnemonic.startswith('.')

ins=[i for i in disasm(0x43F180,2443,skipdata=True) if not is_data(i)]
# find test/cmp followed within 3 insns by a jcc
for k,i in enumerate(ins):
    if i.mnemonic in ('test','cmp'):
        for j in ins[k+1:k+4]:
            if j.mnemonic.startswith('j') and j.mnemonic not in ('jmp',):
                print("%08X %-6s %-38s -> %s %08X"%(i.address,i.mnemonic,i.op_str,j.mnemonic,
                      j.operands[0].imm if j.operands and j.operands[0].type==X86_OP_IMM else 0))
                break
print("\n=== can-place vcall sites and their test ===")
for k,i in enumerate(ins):
    if i.mnemonic=='call' and i.operands and i.operands[0].type==X86_OP_MEM and i.operands[0].mem.disp in (0x1ac,):
        for j in ins[k+1:k+3]:
            print("  %08X call [..+%X] -> %s ; %s"%(i.address,i.operands[0].mem.disp,fmt_insn(j), ""))
