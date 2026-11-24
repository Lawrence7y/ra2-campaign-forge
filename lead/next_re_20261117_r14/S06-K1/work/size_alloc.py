from pehelp import *
import struct
tlo,thi=text_bounds()

# find 'push imm32' where imm  = 0x148 (CellClass) and other candidates
print("=== push 0x148 (CellClass size candidate) in .text ===")
for ins in disasm(tlo, thi-tlo):
    if ins.mnemonic=='push' and ins.operands and ins.operands[0].type==X86_OP_IMM and ins.operands[0].imm==0x148:
        print(f"  {fmt(ins)}")
        for j in disasm(ins.address+ins.size, 20, count=6):
            print("      ",fmt(j))

# MapClass deleting destructor: check vtable slots 0,1,2 functions for push <size>
print("\n=== MapClass vtable slot0/1/2 disasm (look for push size) ===")
for f in [u32(0x7ed404), u32(0x7ed408), u32(0x7ed40c)]:
    print(f"--- {f:#x} ---")
    for ins in disasm(f, 40, count=14):
        print("   ",fmt(ins))
