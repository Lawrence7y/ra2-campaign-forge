from pehelp import *
import struct

# raw dword dump around CellClass RTTI region
print("=== raw dwords 0x7e4eb0..0x7e4f30 (CellClass region) ===")
for va in range(0x7e4eb0, 0x7e4f30, 4):
    d = u32(va)
    sec = section_of(d) if d else None
    print(f"  {va:#x}: {d:#010x}  ({sec[4] if sec else '-'})")

print("\n=== COLs referencing CellClass TD (0x81cd70) ===")
for col in [0x7fcfe0, 0x7fcff8, 0x7fd010, 0x7fd078]:
    print(f"  COL {col:#x}: sig={u32(col):#x} offset={u32(col+4):#x} cd={u32(col+8):#x} "
          f"pTD={u32(col+0xc):#x} pCHD={u32(col+0x10):#x} pSelf={u32(col+0x14):#x}")

print("\n=== disasm slot candidates ===")
for f in [0x410590, 0x410580, 0x4105e0, 0x410300, 0x410260, 0x487e60, 0x487e70, 0x410310]:
    print(f"--- {f:#x} ---")
    for ins in disasm(f, 24, count=8):
        print("   ", fmt(ins))
