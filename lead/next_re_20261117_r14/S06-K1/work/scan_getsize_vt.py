from pehelp import *
import struct

# RTTI name bytes
print("TD MapClass name bytes @0x816bc8:", read(0x816bc8, 24))
print("TD CellClass name bytes @0x81cd78:", read(0x81cd78, 24))

def is_b8c3(f):
    if not f: return None
    b = read(f, 6)
    if len(b)>=6 and b[0]==0xB8 and b[5]==0xC3: return struct.unpack('<I',b[1:5])[0]
    return None

# Scan all dwords in .rdata that look like vtable bases:
# vtable[-4] = COL pointer; COL+0xC -> TD; find slot11=WhatAmI (B8 imm C3) and slot12=GetSize (B8 imm C3)
print("\n=== scan all COLs in .data/.rdata for vtables with slot11 & slot12 both B8 imm32 C3 ===")
found=[]
for secname in ('.rdata','.data'):
    sec = next((s for s in SECTIONS if s[4]==secname),None)
    v,vs,raw,rs,_=sec
    data=pe.get_data(raw,rs)
    for off in range(0, rs-3, 4):
        col=struct.unpack_from('<I',data,off)[0]
        if not (IMAGE_BASE<=col<0x00C00000): continue
        ptd=u32(col+0xC)
        if not ptd: continue
        # TD name = ptd+8
        nm=read(ptd+8, 32)
        if not nm.startswith(b'.?AV'): continue
        vtable=v+off+4
        s11=is_b8c3(u32(vtable+0x2c))
        s12=is_b8c3(u32(vtable+0x30))
        if s11 is not None and s12 is not None:
            found.append((vtable,col,nm.split(b'@')[0],s11,s12))
for vtable,col,nm,s11,s12 in found:
    print(f"  vtable={vtable:#x} COL={col:#x} name={nm.decode('latin1')} WhatAmI={s11} GetSize={s12}(#{s12:#x})")
print("total:",len(found))
