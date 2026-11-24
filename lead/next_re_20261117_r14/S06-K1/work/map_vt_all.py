from pehelp import *
import struct
def looks_getsize(f):
    if not f: return None
    b = read(f, 6)
    if len(b)>=6 and b[0]==0xB8 and b[5]==0xC3: return struct.unpack('<I',b[1:5])[0]
    return None

print("=== MapClass vtable 0x7ed404 all slots (scan 80) ===")
for i in range(0, 80):
    f = u32(0x7ed404 + i*4)
    if not f: 
        print(f"  slot {i}: 0"); continue
    gs = looks_getsize(f)
    sec = section_of(f)
    tag = f'  <== GetSize imm={gs:#x}({gs})' if gs is not None else ''
    print(f"  slot {i:2d} [+{i*4:#04x}] = {f:#010x} ({sec[4] if sec else '-'}){tag}")

print("\n=== xref context 0x56516f / 0x565268 / 0x5652c7 ===")
for va in [0x56516f, 0x565268, 0x5652c7]:
    print(f"--- around {va:#x} ---")
    for ins in disasm(va-12, 28, count=10):
        print("   ", fmt(ins))
