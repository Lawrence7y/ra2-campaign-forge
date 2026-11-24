from pehelp import *
import struct
# GetCellAt 0x5657A0 full-ish disassembly
print("=== GetCellAt @ 0x5657A0 ===")
for ins in disasm(0x5657A0, 0x120, count=80):
    print("   ", fmt(ins))
