from pehelp import *
import struct
col=u32(0x7eff54-4)
print(f"COL@0x7eff50 = {col and hex(col)}")
if col:
    ptd=u32(col+0xc)
    print(f"  offset={u32(col+4):#x} pTD={ptd and hex(ptd)} name={read(ptd+8,50) if ptd else b''}")
    chd=u32(col+0x10); print(f"  pCHD={chd and hex(chd)}")
