from pehelp import *
import struct
def is_b8c3(f):
    if not f: return None
    b=read(f,6)
    if len(b)>=6 and b[0]==0xB8 and b[5]==0xC3: return struct.unpack('<I',b[1:5])[0]
    return None
# scan entire vtable extent until non-text pointers dominate
print("=== MapClass vtable all slots that are B8 imm32 C3 ===")
vt=0x7ed404
last=0
for i in range(0,400):
    f=u32(vt+i*4)
    if not f: continue
    s=section_of(f)
    if not s or s[4]!='.text': 
        # keep scanning a bit past rdata ptrs
        continue
    last=i
    gs=is_b8c3(f)
    if gs is not None:
        print(f"  slot {i} [+{i*4:#x}] -> {f:#x} returns {gs} (#{gs:#x})")
print("last text slot index:", last)
