import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditlib import *

VT = 0x007F794C

print("=== A) tail of 007B10C0 from 0x7B1356 ===")
dump(0x7B1356, 0x90)

print()
print("=== B) host function of write site 007B0DA4 -> dump from 007B0D90 ===")
dump(0x007B0D90, 0xB0)

print()
print("=== C) ALL imm32 occurrences of 0x7F794C in the whole image ===")
hits = find_u32_va(VT)
print(f"count = {len(hits)}")
for h in hits:
    print(f"   {h:08X}  ctx={hexb(h-8,16)}  next={u32(h):08X}")
