# -*- coding: utf-8 -*-
"""R128 公共读取层：按 VA 直接读映像字节（简单、可复用、不猜）。"""
import os, struct, pefile
ROOT='/home/t628/projects/ra2-campaign-forge'
EXE=os.path.join(ROOT,'ra2bench','gamemd.exe')
pe=pefile.PE(EXE)
IB=pe.OPTIONAL_HEADER.ImageBase
SECS=[]
for s in pe.sections:
    lo=IB+s.VirtualAddress
    SECS.append((s.Name.decode().strip('\x00'), lo, lo+max(s.Misc_VirtualSize,s.SizeOfRawData),
                 s.PointerToRawData, s.Misc_VirtualSize, s.SizeOfRawData))
def secof(va):
    for n,lo,hi,ptr,vs,rs in SECS:
        if lo<=va<hi: return n
    return None
def rd(va,n):
    for nm,lo,hi,ptr,vs,rs in SECS:
        if lo<=va<hi:
            off=va-lo
            if off>=rs: return b''
            av=min(n,rs-off)
            return pe.__data__[ptr+off:ptr+off+av]
    return None
def u32(va):
    b=rd(va,4)
    if b is None or len(b)<4: return None
    return struct.unpack('<I',b)[0]
def i32(va):
    b=rd(va,4)
    if b is None or len(b)<4: return None
    return struct.unpack('<i',b)[0]
def cstr(va,n=256):
    b=rd(va,n)
    if not b: return None
    z=b.find(b'\x00')
    return b[:z if z>=0 else len(b)].decode('latin-1')
def gt(va):
    b=rd(va,16)
    if b is None or len(b)<16: return None
    d1,d2,d3=struct.unpack('<IHH',b[:8])
    return '{%08X-%04X-%04X-%s-%s}'%(d1,d2,d3,b[8:10].hex().upper(),b[10:16].hex().upper())
def col_of(vt):
    """给定 vtable VA，返回 COL 五字段（MSVC x86 RTTI，COL 在 vt-4 处）。"""
    c=u32(vt-4)
    if c is None: return None
    chd=u32(c+16)
    if chd is None: return None
    n=u32(chd+8); arr=u32(chd+12)
    if n is None or arr is None or n>64: return None
    bases=[]
    for i in range(n):
        bcd=u32(arr+4*i)
        if bcd is None: return None
        td=u32(bcd)
        if td is None: return None
        bases.append({'name':cstr(td+8,200),'ncb':u32(bcd+4),'mdisp':i32(bcd+8)})
    return {'signature':u32(c),'type_desc':cstr(u32(c+12)+8,200) if u32(c+12) else None,
            'pTypeDescriptor':u32(c+12),'pClassDescriptor':chd,'n':n,'bases':bases}
