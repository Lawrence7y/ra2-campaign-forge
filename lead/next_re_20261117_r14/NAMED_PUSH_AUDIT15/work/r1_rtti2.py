import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditlib import *

VT  = 0x007F794C
COL = 0x0080EA60

def col_info(col_va):
    print(f"COL @{col_va:08X} raw = {rd(col_va,20).hex()}")
    sig, off_, cd = u32(col_va), u32(col_va+4), u32(col_va+8)
    ptd, pch = u32(col_va+12), u32(col_va+16)
    print(f"  signature={sig} (expect 0)  offset={off_}  cdOffset={cd}  pTD={ptd:08X}  pCHD={pch:08X}")
    return sig, off_, cd, ptd, pch

sig, off_, cd, ptd, pch = col_info(COL)

print()
print(f"=== TD @{ptd:08X} (virtual-space VA) ===")
print(f"  raw {rd(ptd,0x20).hex()}")
print(f"  pVFTable={u32(ptd):08X}  spare={u32(ptd+4):08X}")
name = cstring(ptd+8)
print(f"  name = '{name}'")

print()
print(f"=== CHD @{pch:08X} ===")
print(f"  raw {rd(pch,0x18).hex()}")
print(f"  sig={u32(pch)} attr={u32(pch+4)} pTD={u32(pch+8):08X} pCHDnext={u32(pch+12):08X}")
nxt = u32(pch+12)
depth=0
while nxt and depth < 8:
    print(f"  -> CHD @{nxt:08X} sig={u32(nxt)} attr={u32(nxt+4)} pTD={u32(nxt+8):08X} name='{cstring(u32(nxt+8)+8)}'")
    nxt = u32(nxt+12); depth+=1
