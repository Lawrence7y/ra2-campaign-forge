from pehelp import *
import struct
# find COL for vtable 0x7e6114: dword at 0x7e6110 should be COL
col=u32(0x7e6114-4)
print(f"COL@0x7e6110 = {col and hex(col)}")
if col:
    ptd=u32(col+0xc)
    print(f"  offset={u32(col+4):#x} pTD={ptd and hex(ptd)} name={read(ptd+8,40) if ptd else b''}")
    chd=u32(col+0x10); print(f"  pCHD={chd and hex(chd)}")
# also scan for all vtables near 0x7e6114 and their names
print("\nscan all COLs whose vtable in 0x7e6000..0x7e6200:")
for secname in ('.rdata','.data'):
    sec=next((s for s in SECTIONS if s[4]==secname),None)
    v,vs,raw,rs,_=sec
    data=pe.get_data(raw,rs)
    for off in range(0,rs-3,4):
        c=struct.unpack_from('<I',data,off)[0]
        if not (IMAGE_BASE<=c<0x00C00000): continue
        vt=v+off+4
        if 0x7e6000<=vt<0x7e6200:
            ptd=u32(c+0xc)
            nm=read(ptd+8,40).split(b'@')[0] if ptd and u32(ptd+8) else b'?'
            print(f"  vt={vt:#x} COL={c:#x} off={u32(c+4):#x} name={nm!r}")

# who writes 0x7e6114 and who calls 0x4a8730
print("\n.text xrefs to 0x7e6114 immediate:")
import struct as st
pat=st.pack('<I',0x7e6114)
for x in find_bytes(pat, section='.text'):
    print(f"  {x:#x}")
