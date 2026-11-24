#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent RTTI verification: vtable VA -> vtable[-1] COL -> TypeDescriptor -> mangled name.
Pure pefile raw-byte parse; no atlas / vtables.json dependency.  Read-only.
"""
import struct, sys
import pefile
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(EXE, fast_load=True)
BASE=pe.OPTIONAL_HEADER.ImageBase
# Build VA -> file offset across all sections
segs=[]
for s in pe.sections:
    va=BASE+s.VirtualAddress
    segs.append((va, va+max(s.Misc_VirtualSize,s.SizeOfRawData), s.PointerToRawData, s.SizeOfRawData))

def va2off(va):
    for (lo,hi,raw,sz) in segs:
        if lo<=va<lo+sz:
            return raw+(va-lo)
    return None

def rd32(va):
    o=va2off(va)
    if o is None: return None
    with open(EXE,'rb') as f:
        f.seek(o); b=f.read(4)
    return struct.unpack('<I',b)[0] if len(b)==4 else None

def read_cstr(va, maxn=128):
    o=va2off(va)
    if o is None: return None
    with open(EXE,'rb') as f:
        f.seek(o); b=f.read(maxn)
    z=b.find(b'\x00')
    return b[:z].decode('latin-1') if z>=0 else b.decode('latin-1')

def rtti(vtva):
    col=rd32(vtva-4)
    print("vtable   = 0x%08X"%vtva)
    print("vtable[-1] (COL) = %s"%(("0x%08X"%col) if col else None))
    if not col: return
    sig=rd32(col); off=rd32(col+4); cd=rd32(col+8); td=rd32(col+0xC); pcd=rd32(col+0x10)
    print("COL sig=%s offset=%s cdOffset=%s pTypeDescriptor=%s pClassDescriptor=%s"%(
        sig, off, cd, ("0x%08X"%td) if td else None, ("0x%08X"%pcd) if pcd else None))
    if td:
        td_vf=rd32(td); td_spare=rd32(td+4); name=read_cstr(td+8)
        print("TD  vftable=%s spare=%s name=%r"%(("0x%08X"%td_vf) if td_vf else None, td_spare, name))

if __name__=="__main__":
    for a in sys.argv[1:]:
        rtti(int(a,16)); print()
