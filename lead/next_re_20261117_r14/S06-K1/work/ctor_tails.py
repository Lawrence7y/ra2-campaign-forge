from pehelp import *
print("=== CellClass ctor tail 0x47bd90..0x47be40 ===")
for ins in disasm(0x47bd90, 0xb0, count=50):
    print("   ",fmt(ins))
print("\n=== MapClass ctor wrapper 0x4a8730 full ===")
for ins in disasm(0x4a8730, 0x60, count=30):
    print("   ",fmt(ins))
