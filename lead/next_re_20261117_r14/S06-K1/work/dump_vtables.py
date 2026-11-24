from pehelp import *
import struct

VT = {
 'CellClass': [0x7e4ec0, 0x7e4ec8, 0x7e4ed0, 0x7e4eec],
 'MapClass': [0x7ed404],
}

def slotfunc(va):
    f = u32(va)
    if not f: return None
    s = section_of(f)
    return (f, s[4] if s else None)

def looks_getsize(f):
    """GetSize = B8 <imm32> C3 (mov eax,imm32; ret)."""
    if not f: return None
    b = read(f, 6)
    if len(b) == 6 and b[0] == 0xB8 and b[5] == 0xC3:
        return struct.unpack('<I', b[1:5])[0]
    return None

for cls, vts in VT.items():
    for vt in vts:
        print(f"===== {cls} vtable {vt:#x} =====")
        for i in range(0, 40):
            f, sec = slotfunc(vt + i*4) or (None, None)
            gs = looks_getsize(f)
            tag = f' <== GetSize imm32={gs:#x}' if gs is not None else ''
            print(f"  slot {i:2d} [+{i*4:#04x}] = {f and hex(f):>12} ({sec}){tag}")
        print()

print("InvalidCell clue check: u32(0xABDC50) =", hex(u32(0xABDC50) or 0))
print("MapClass singleton u32(0x87F7E8) =", hex(u32(0x87F7E8) or 0))
