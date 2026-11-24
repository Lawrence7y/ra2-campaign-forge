from pehelp import *
print("=== constructor 0x565076..0x565184 (first 60 instr) ===")
for ins in disasm(0x565076, 0x110, count=80):
    print("   ", fmt(ins))
