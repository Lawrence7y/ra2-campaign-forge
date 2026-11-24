# -*- coding: utf-8 -*-
"""终检 row1 00432050 ③b④：确证回边、边界检查、循环体内非栈写三者的控制流归属。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
ins = R.disasm_body(0x432050, 584)
A = {i.address: i for i in ins if i.id}
# 回边
print("back-edge 0043224A:", A[0x43224A].mnemonic, A[0x43224A].op_str, "|", A[0x43224C].mnemonic, A[0x43224C].op_str)
# 边界检查链
for va in (0x4320B9,0x4320BC,0x4320C1,0x4320C3,0x4320C5,0x4320C7,0x4320C9):
    print("bound %08X: %s %s"%(va,A[va].mnemonic,A[va].op_str))
# 循环体内非栈写（esi=this）：列出 4320B9..43224C 之间所有 mov [esi+..],reg/imm
print("\nin-loop non-stack writes to [esi+..] (esi=this, heap object):")
for i in ins:
    if not i.id or not (0x4320B9 <= i.address <= 0x43224C):
        continue
    if i.id==R.X86_INS_MOV and len(i.operands)==2:
        a,b=i.operands
        if a.type==R.X86_OP_MEM and a.mem.base==R.X86_REG_ESI:
            print("  %08X %s %s"%(i.address,i.bytes.hex(),i.mnemonic+" "+i.op_str))
# I/O calls in loop
print("\nin-loop calls:")
for i in ins:
    if not i.id or not (0x4320B9 <= i.address <= 0x43224C):
        continue
    if i.id==R.X86_INS_CALL:
        print("  %08X %s %s"%(i.address,i.bytes.hex(),i.mnemonic+" "+i.op_str))
