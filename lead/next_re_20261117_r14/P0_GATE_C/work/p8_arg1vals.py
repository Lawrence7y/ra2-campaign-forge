# -*- coding: utf-8 -*-
"""Arg1 value set: dump 20 bytes before each direct E8 call to gate fn 47C620."""
import pefile
from capstone import *
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data=open(EXE,'rb').read();pe=pefile.PE(EXE,fast_load=True);BASE=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    nm=s.Name.rstrip(b"\x00").decode('latin1');secs.append((nm,BASE+s.VirtualAddress,s.PointerToRawData,s.SizeOfRawData,s.Misc_VirtualSize))
def rd(va,n):
    for nm,v,r,rs,vs in secs:
        if v<=va<v+max(vs,rs): return data[r+(va-v):r+(va-v)+n]
    return b''
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
def dis(start,end):
    va=start
    while va<end:
        g=list(md.disasm(rd(va,16),va,count=1))
        if not g: va+=1;continue
        i=g[0];print("    %08X %-7s %s"%(i.address,i.mnemonic,i.op_str));va+=i.size
for c in [0x43F2AE,0x449482,0x47EE93,0x58865F,0x58886E,0x5FC6FA,0x6D5A98,0x6D5D33,0x716209,0x71C554]:
    print("\n=== call@%08X ==="%c);dis(c-0x20,c+4)
