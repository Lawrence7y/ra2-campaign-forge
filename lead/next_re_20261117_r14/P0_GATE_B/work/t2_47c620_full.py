#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Full linear disassembly of 0x47C620 until first `ret`, plus stack-arg analysis."""
import sys
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_GATE_B\work')
import peutil
from peutil import *

BASE = 0x47C620
MAXB = 0x400  # 1024 bytes
def is_data(i): return i.id==0 or i.mnemonic.startswith('.')

insns = []
for insn in disasm(BASE, MAXB, skipdata=True):
    insns.append(insn)
    if insn.mnemonic in ('ret','retf') and not is_data(insn):
        break

print("0x47C620 full disassembly (%d insns, end @ 0x%08X):" % (len(insns), insns[-1].address+insns[-1].size))
for insn in insns:
    print(fmt_insn(insn))

print()
print("=== [esp+N] references in 0x47C620 ===")
for insn in insns:
    if is_data(insn): continue
    for op in insn.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_ESP:
            print("  %08X %s %s  ; disp=%d" % (insn.address, insn.mnemonic, insn.op_str, op.mem.disp))
