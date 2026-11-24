from pehelp import *
print("=== 0x485020 (ore value per cell) full disasm ===")
for ins in disasm(0x485020, 0x200, count=140):
    print("   ", fmt(ins))
