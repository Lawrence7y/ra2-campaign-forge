# -*- coding: utf-8 -*-
"""Check caller context 0x6C4ACC (virtual dispatch to 4CCA20 region) and COL+0x10 of FlyLocomotionClass."""
import pefile,struct
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data=open(EXE,'rb').read();pe=pefile.PE(EXE,fast_load=True);BASE=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    nm=s.Name.rstrip(b"\x00").decode('latin1');secs.append((nm,BASE+s.VirtualAddress,s.PointerToRawData,s.SizeOfRawData,s.Misc_VirtualSize))
def rd(va,n):
    for nm,v,r,rs,vs in secs:
        if v<=va<v+max(vs,rs):return data[r+(va-v):r+(va-v)+n]
    return b''
def u32(va):
    b=rd(va,4);return struct.unpack('<I',b)[0] if len(b)==4 else None
print("COL 0x800658: sig=%08X off=%08X ctor=%08X TD=%08X vptr=%08X"%(u32(0x800658),u32(0x80065c),u32(0x800660),u32(0x800664),u32(0x800668)))
from capstone import *
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
def dis(s,e):
    va=s
    while va<e:
        g=list(md.disasm(rd(va,16),va,count=1))
        if not g: va+=1;continue
        i=g[0];print("  %08X %-7s %s"%(i.address,i.mnemonic,i.op_str));va+=i.size
print("\n0x6C4ACC context:")
dis(0x6C4AB0,0x6C4AE0)
