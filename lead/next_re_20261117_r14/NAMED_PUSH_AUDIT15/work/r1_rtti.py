import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditlib import *

VT = 0x007F794C
COL = 0x0080EA60

def parse_col_at(col_va):
    sig = u32(col_va + 0)
    off_ = u32(col_va + 4)
    cd  = u32(col_va + 8)
    ptd = u32(col_va + 12)
    pch = u32(col_va + 16)
    print(f"COL @{col_va:08X} raw = {rd(col_va,20).hex()}")
    print(f"  signature={sig} (expect 0)  offset={off_}  cdOffset={cd}  pTD_rva=0x{ptd:X}  pCHD_rva=0x{pch:X}")
    td = IB + ptd
    print(f"  TD @{td:08X} raw={rd(td,0x18).hex()}")
    print(f"    pVFTable = {u32(td):08X}   spare = {u32(td+4):08X}")
    print(f"    name     = '{cstring(td+8)}'")
    if pch:
        chd = IB + pch
        print(f"  CHD @{chd:08X} raw={rd(chd,0x10).hex()}")
        print(f"    signature={u32(chd)} attr={u32(chd+4)} pTD={u32(chd+8):08X} pCHDnext={u32(chd+12):08X}")
        nxt = u32(chd+12)
        if nxt: print(f"    -> CHD chain2 @{nxt:08X} name='{cstring(u32(nxt+8)+8) if u32(nxt+8) else ''}'")
    return sig, off_

sig, off_ = parse_col_at(COL)

print()
print("=== TD name also via vt[-3] style? check COL identical for other vtables ===")
# find all 4-byte occurrences of COL pointer value across image (candidates of vt-4 slots)
hits = find_u32_va(COL)
print(f"occurrences of COL ptr {COL:08X}: {len(hits)}")
for h in hits[:40]:
    print(f"   @{h:08X}  next u32 (candidate vt) = {u32(h+4):08X}")
