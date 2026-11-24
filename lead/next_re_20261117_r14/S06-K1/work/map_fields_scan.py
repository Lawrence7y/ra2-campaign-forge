from pehelp import *
import struct, collections
from capstone.x86 import X86_OP_REG
BASE=0x87f7e8
tlo,thi=text_bounds()

abs_off=collections.Counter()
base_regs=set()
reg_off=collections.Counter()
for ins in disasm(tlo, thi-tlo):
    if ins.id==0:  # skipdata pseudo-instruction
        continue
    ops=ins.operands
    for op in ops:
        if op.type==X86_OP_MEM and op.mem.base==0 and op.mem.disp and BASE<=op.mem.disp<BASE+0x3000:
            abs_off[op.mem.disp-BASE]+=1
    if ins.mnemonic=='mov' and len(ops)>=2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_IMM and ops[1].imm==BASE:
        base_regs.add(ops[0].reg)
    for op in ops:
        if op.type==X86_OP_MEM and op.mem.base in base_regs and 0<=op.mem.disp<0x3000:
            reg_off[op.mem.disp]+=1
    if ins.mnemonic=='ret': base_regs.clear()

print("=== absolute [0x87F7E8+disp] accesses ===")
for off,c in sorted(abs_off.items()):
    print(f"  +{off:#05x} ({c})")
print("\n=== mov reg,0x87F7E8 -> [reg+disp] accesses ===")
for off,c in sorted(reg_off.items()):
    print(f"  +{off:#05x} ({c})")
maxabs=max(abs_off) if abs_off else 0
maxreg=max(reg_off) if reg_off else 0
print(f"\nmax absolute disp = +{maxabs:#x}; max reg disp = +{maxreg:#x}")
