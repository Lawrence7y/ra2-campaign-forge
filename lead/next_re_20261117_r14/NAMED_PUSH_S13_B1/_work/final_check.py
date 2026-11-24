# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C2
from capstone.x86 import X86_OP_IMM

def show(a,b):
    for ins in R.disasm(a, R.read_va(a,b-a)):
        print("    %08X  %-20s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

print("### 004684E0 head")
show(0x004684E0, 0x00468530)
print("\n### container at 0x89de18 / its vtable")
vtptr=C2.u32(0x89DE18); print("  [0x89DE18]=%08X" % (vtptr or 0))
if vtptr:
    print("  vt[0x10]=%08X" % (C2.u32(vtptr+0x10) or 0))
    c=C2.parse_col(C2.u32(vtptr-4)); print("  COL=%08X sig=%s" % ((C2.u32(vtptr-4) or 0), c["sig"] if c else None))
    if c:
        td=C2.parse_td(c["td"]); print("  name=%s" % (td["name"] if td else None))

print("\n### 00468670 call/test/jcc sites")
ins=R.disasm_body(0x00468670, 1304)
for i,insn in enumerate(ins):
    if insn.mnemonic=="call":
        for k in range(i+1,min(i+5,len(ins))):
            if ins[k].mnemonic in ("test","cmp") and k+1<len(ins) and ins[k+1].mnemonic.startswith("j"):
                callee = "%08X"%(insn.operands[0].imm & 0xFFFFFFFF) if insn.operands and insn.operands[0].type==X86_OP_IMM else "indirect"
                print("  call@%08X->%s ; %s@%08X ; %s@%08X" % (
                    insn.address,callee,ins[k].mnemonic,ins[k].address,ins[k+1].mnemonic,ins[k+1].address))
                break

print("\n### 0x4C93D0 return profile")
print(" ", R.callee_return_profile(0x4C93D0))
print("### 0x7C8E17 return profile")
print(" ", R.callee_return_profile(0x7C8E17))

print("\n### 0075E510 first 90 bytes")
show(0x0075E510, 0x0075E57A)
