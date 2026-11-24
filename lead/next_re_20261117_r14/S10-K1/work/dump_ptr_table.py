#!/usr/bin/env python3
"""S10-K1: dump the string-pointer table in 0x816C80..0x816D30 and deref each entry."""
import struct
import pefile
EXE=r"ra2youli\gamemd.exe"
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
data=open(EXE,'rb').read()
secs=[]
for s in pe.sections:
    secs.append((s.Name.decode(errors='replace').rstrip('\x00'), IB+s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
def va2off(va):
    for n,v,vs,r,rs in secs:
        if v<=va<v+max(vs,rs): return r+(va-v)
    return None
def off2va(o):
    for n,v,vs,r,rs in secs:
        if r<=o<r+rs: return v+(o-r)
    return None
def cstr(va):
    o=va2off(va)
    if o is None: return None
    e=o
    while e<len(data) and data[e]!=0 and e-o<120: e+=1
    try: return data[o:e].decode('ascii')
    except: return None

# dump qwords/pointers from 0x816C60 to 0x816D2C
print("=== pointer table region 0x816C60..0x816D2C (as 4-byte LE) ===")
for va in range(0x816C60,0x816D2C,4):
    o=va2off(va)
    val=struct.unpack_from('<I',data,o)[0]
    s=cstr(val) if 0x816000<val<0x82A000 else None
    print("  [%08X] = 0x%08X  %s" % (va,val, repr(s) if s else ''))
