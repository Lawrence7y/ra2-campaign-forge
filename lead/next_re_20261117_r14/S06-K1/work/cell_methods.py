from pehelp import *
import struct
VT=0x7e4eec
print("=== CellClass vtable method map (slots 0..34) ===")
for i in range(0,35):
    f=u32(VT+i*4)
    print(f"  vt{i:2d} = {f:#x}")

for addr,label in [(0x47ff80,'getcenter 0x47ff80'),(0x485200,'vt3/0x485200'),(0x485060,'0x485060 range-check')]:
    print(f"\n=== {label} ===")
    for ins in disasm(addr, 0x100, count=60):
        print("   ",fmt(ins))
        if ins.mnemonic=='ret': break
