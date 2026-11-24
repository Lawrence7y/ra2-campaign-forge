from pehelp import *
import struct

def looks_getsize(f):
    if not f: return None
    b = read(f, 6)
    if len(b) >= 6 and b[0] == 0xB8 and b[5] == 0xC3:
        return struct.unpack('<I', b[1:5])[0]
    return None

def describe_vt(vt, label, n=16):
    print(f"== {label} primary vtable {vt:#x} ==")
    for i in range(n):
        f = u32(vt + i*4)
        if not f: 
            print(f"  slot {i:2d} = 0"); continue
        gs = looks_getsize(f)
        tag = f'  <== GetSize={gs:#x}({gs})' if gs is not None else ''
        sec = section_of(f)
        print(f"  slot {i:2d} [+{i*4:#04x}] = {f:#010x} ({sec[4] if sec else '-'}){tag}")

print("--- object vptr checks ---")
for obj in [0xABDC50, 0x87F7E8]:
    print(f"  u32({obj:#x}) = {u32(obj) and hex(u32(obj))}")

# MapClass COL
col = 0x8054c8
print(f"\nMapClass COL {col:#x}: sig={u32(col):#x} offset={u32(col+4):#x} pTD={u32(col+0xc):#x} pCHD={u32(col+0x10):#x}")
print("MapClass vtable candidates raw:")
for va in range(0x7ed400-8, 0x7ed404+0x60, 4):
    d = u32(va)
    sec = section_of(d) if d else None
    mark = ' <--COLref' if d == col else ''
    print(f"  {va:#x}: {d:#010x} ({sec[4] if sec else '-'}){mark}")

describe_vt(0x7e4eec, 'CellClass', 16)
describe_vt(0x7ed404, 'MapClass', 16)
