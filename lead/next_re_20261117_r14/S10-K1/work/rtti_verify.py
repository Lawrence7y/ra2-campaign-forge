#!/usr/bin/env python3
"""S10-K1: verify RTTI TD chain (MSVC COL: pTypeInfo at +0xC)."""
import struct, pefile
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
def rd(va): return struct.unpack_from('<I',data,va2off(va))[0]
def cstr(va):
    o=va2off(va); e=o
    while e<len(data) and data[e]!=0 and e-o<90: e+=1
    return data[o:e].decode('ascii',errors='replace')
for vname,base in [('MissionClass',0x7EDCC0),('FootClass',0x7E8C94),('RadioClass',0x7F0508),
                   ('TechnoClass',0x7F4960),('InfantryClass',0x7EB058),('AircraftClass',0x7E22A4),
                   ('BuildingClass',0x7E3EBC)]:
    col=rd(base-4)
    td=rd(col+0xC)
    print("%-14s vt=0x%X COL=0x%X TD=0x%X name=%r"%(vname,base,col,td,cstr(td+16) if 0x7E1000<td<0x811000 else '?'))
