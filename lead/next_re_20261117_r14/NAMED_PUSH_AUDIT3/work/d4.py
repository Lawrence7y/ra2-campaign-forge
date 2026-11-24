import struct
from core import *

VT = 0x007F6218

def rtti(vt):
    print("--- RTTI chain for vt %08X ---" % vt)
    col = u32(vt - 4)
    print("vt-4 (COL) = %08X  (%s / %s)" % (col, hex(col) if col else "-", sec_of(col) if col else "-"))
    if not col:
        return
    sig = u32(col)
    print("  COL.sig(+0x00) = %08X  (expect 0)" % sig)
    td = u32(col + 0xC)
    print("  COL.TD(+0x0C)  = %08X" % td)
    nm_ptr = u32(td + 8)
    print("  TD+8 name ptr  = %08X" % nm_ptr)
    raw = read(nm_ptr, 64)
    print("  name raw       = %r" % raw.split(b"\x00")[0])
    print("  COL raw16      = %s" % read(col, 16).hex(" "))
    print("  TD  raw28      = %s" % read(td, 28).hex(" "))

rtti(VT)
print()
for base, lbl in ((0x007F6218, "primary vt (+0)"), (0x007F61FC, "sec vt (+4)"), (0x007F61F4, "sec vt (+8)"), (0x007F61EC, "sec vt (+0xC)")):
    print("=== %s @ %08X : refcount/cols before, slots after ===" % (lbl, base))
    print("  [vt-12..vt-4] = %s" % read(base - 12, 12).hex(" "))
    for i in range(0, 20):
        v = u32(base + i * 4)
        print("   slot%-2d (+0x%02X) = %08X  %s" % (i, i * 4, v, sec_of(v) if v else "-"))
    print()
