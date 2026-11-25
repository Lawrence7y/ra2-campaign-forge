# -*- coding: utf-8 -*-
import os, struct, pefile
ROOT='/home/t628/projects/ra2-campaign-forge'
EXE=os.path.join(ROOT,'ra2bench','gamemd.exe')
pe=pefile.PE(EXE); IB=pe.OPTIONAL_HEADER.ImageBase
def sect(va):
    for s in pe.sections:
        lo=IB+s.VirtualAddress; hi=lo+s.Misc_VirtualSize
        if lo<=va<hi: return s
    return None
def rd(va,n):
    s=sect(va)
    if not s: return None
    off=va-(IB+s.VirtualAddress)
    return pe.get_data(s.VirtualAddress+off,n)
def u32(va):
    b=rd(va,4)
    return None if b is None or len(b)<4 else struct.unpack('<I',b)[0]
def cstr(va,n=200):
    b=rd(va,n)
    if b is None: return None
    z=b.find(b'\x00')
    return b[:z if z>=0 else n].decode('latin-1')
def gt(va):
    b=rd(va,16)
    if b is None: return None
    d1,d2,d3=struct.unpack('<IHH',b[:8])
    return '{%08X-%04X-%04X-%s-%s}'%(d1,d2,d3,b[8:10].hex().upper(),b[10:16].hex().upper())

for name,va in [('0x7ea6e8',0x7ea6e8),('0x7e36c0',0x7e36c0),('0x7e9b20',0x7e9b20),
                ('0x87f7e8',0x87f7e8),('0x7ea564',0x7ea564),('0x7f4108',0x7f4108),
                ('0x7e36d4',0x7e36d4)]:
    s=sect(va)
    print('%-10s sect=%-8s u32=%s' % (name, s.Name.decode().strip('\x00') if s else None,
          '0x%08x'%u32(va) if u32(va) is not None else None))
print()
print('0x7ea6e8 GUID =', gt(0x7ea6e8))
print('0x87f7e8 raw16 =', rd(0x87f7e8,16).hex())
print('0x87f7e8 vptr  =', '0x%08x'%u32(0x87f7e8))
print('0x87f7e8+4     =', '0x%08x'%u32(0x87f7e8+4))
print('0x87f7e8+8     =', '0x%08x'%u32(0x87f7e8+8))
print('0x87f7e8+12    =', '0x%08x'%u32(0x87f7e8+12))
