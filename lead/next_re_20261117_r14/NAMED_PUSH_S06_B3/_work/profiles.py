# -*- coding: utf-8 -*-
"""Verify callee return profiles + byte-level anchors for candidate PASS rows."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R

for va in [0x5F9720, 0x5F9950, 0x4103E0, 0x410320, 0x410380, 0x7514D0, 0x5FDD20]:
    p = R.callee_return_profile(va)
    print("%08X -> %s" % (va, p))

print("=" * 80)
# Find the E_POINTER mov and Read/Write slot call inside 0x5F9720 body (atlas 256)
code = R.read_va(0x5F9720, R.ATLAS.get("005F9720", {}).get("size", 256))
insns = R.disasm(0x5F9720, code)
for ins in insns:
    if ins.id == 0: continue
    if (ins.id == R.X86_INS_MOV and ins.operands and ins.operands[0].type == R.X86_OP_REG
        and ins.operands[0].reg == R.X86_REG_EAX and ins.operands[1].type == R.X86_OP_IMM):
        print("  5F9720 eax imm @%08X: %s" % (ins.address, ins.op_str))
    if ins.id == R.X86_INS_CALL:
        print("  5F9720 call @%08X: %s" % (ins.address, ins.op_str))
