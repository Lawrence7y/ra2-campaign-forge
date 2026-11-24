# -*- coding: utf-8 -*-
"""probe: dump the real RTTI layout for a vtable whose COL/TD COMMON names explicitly:
   InfantryClass: vt 0x7EB058, vt-4 = 0x7EB054 = 0x8033B8 (COL, pTD=0x825508, TD+8='.?AVInfantryClass@@')
"""
import struct
import sys
import os

import pefile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_survey as L

IMG = open(L.EXE, "rb").read()
PE = pefile.PE(L.EXE, fast_load=True)
IBS = PE.OPTIONAL_HEADER.ImageBase
SECS = [(s.Name.rstrip(b"\x00").decode("latin1"), IBS + s.VirtualAddress,
         s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData) for s in PE.sections]


def offof(va):
    for nm, sva, vs, rs, ro in SECS:
        if sva <= va < sva + rs:
            return ro + (va - sva)
    return None


def rd32(va):
    o = offof(va)
    return struct.unpack_from("<I", IMG, o)[0] if o is not None else None


def dump(va, n=32, label=""):
    o = offof(va)
    if o is None:
        print("%s 0x%08X: <unmapped>" % (label, va))
        return
    b = IMG[o:o + n]
    print("%s 0x%08X: %s" % (label, va, b.hex(" ")))
    for k in range(0, n, 4):
        print("        +%02X = 0x%08X" % (k, struct.unpack_from("<I", b, k)[0]))


print("=== around the InfantryClass vtable head (vt-8 .. vt+16) ===")
dump(0x007EB048, 32, "head")
print()
print("=== COL 0x8033B8 ===")
dump(0x008033B8, 24, "col")
print()
print("=== TD 0x825508 ===")
dump(0x00825508, 40, "td")
o = offof(0x00825508)
print("   name bytes at TD+8:", IMG[o + 8:o + 8 + 40])
print()
print("=== also check vt-8 and vt-4 as dwords ===")
print("  [0x7EB058-8] = 0x%08X" % rd32(0x007EB050))
print("  [0x7EB058-4] = 0x%08X" % rd32(0x007EB054))
print("  [0x7EB058+0] = 0x%08X" % rd32(0x007EB058))

print("\n=== how many dwords in .rdata point at a 'plausible COL' (sig 0, +0xC in .rdata, TD+8='.?A') ===")
RD = [s for s in SECS if s[0] == ".rdata"][0]
RSTART, RLEN, RRO = RD[1], RD[3], RD[4]
cnt = 0
for off in range(0, RLEN - 4, 4):
    colp = struct.unpack_from("<I", IMG, RRO + off)[0]
    if not (RSTART <= colp < RSTART + RLEN):
        continue
    if rd32(colp) != 0:
        continue
    td = rd32(colp + 0xC)
    if td is None:
        continue
    nm = IMG[offof(td) + 8:offof(td) + 12] if offof(td) else b""
    if nm.startswith(b".?A"):
        cnt += 1
        if cnt <= 5:
            print("  table head 0x%08X -> COL 0x%08X TD 0x%08X  name=%r"
                  % (RSTART + off + 4, colp, td, IMG[offof(td) + 8:offof(td) + 40]))
print("  count:", cnt)
