import struct
from core import *

def show(lo, hi, title):
    print("=== %s [%08X,%08X) ===" % (title, lo, hi))
    for l in dis_lines(lo, hi):
        print(l)
    print()

LIVE = 0x007EA2A4
DEAD = 0x007EA2C4
for vt, lbl in ((LIVE, "container LIVE vt"), (DEAD, "container DEAD vt")):
    print("=== %s @ %08X ===" % (lbl, vt))
    print("  [vt-4] COL = %08X" % u32(vt - 4))
    col = u32(vt - 4)
    if col:
        td = u32(col + 0xC)
        nm = read(td + 8, 64).split(b"\x00")[0]
        print("  COL.sig=%08X TD=%08X name=%r" % (u32(col), td, nm))
    for i in range(0, 10):
        print("   slot%d (+0x%02X) = %08X" % (i, i * 4, u32(vt + i * 4)))
    print()

find = u32(LIVE + 0x10)
print("Find (live +0x10) = %08X" % find)
show(find, find + 0x30, "container Find")

for name, va in (("base ctor? 0x710AF0", 0x710AF0), ("ctor? 0x711840", 0x711840), ("base dtor? 0x711AE0", 0x711AE0),
                 ("operator delete? 0x7C8B3D", 0x7C8B3D), ("singleton release? 0x7258D0", 0x7258D0),
                 ("0x7162F0", 0x7162F0), ("0x410230", 0x410230)):
    show(va, va + 0x40, name)
