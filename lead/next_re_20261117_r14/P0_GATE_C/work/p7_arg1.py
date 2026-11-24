# -*- coding: utf-8 -*-
"""Where is arg1 ([esp+0x1c] at entry / [ebp+8]) used in gate fn? And direct callers of 47C620."""
import pefile, struct
from capstone import *
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data=open(EXE,'rb').read()
pe=pefile.PE(EXE,fast_load=True);BASE=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    nm=s.Name.rstrip(b"\x00").decode("latin1");secs.append((nm,BASE+s.VirtualAddress,s.PointerToRawData,s.SizeOfRawData,s.Misc_VirtualSize))
def rd(va,n):
    for nm,v,r,rs,vs in secs:
        if v<=va<v+max(vs,rs): return data[r+(va-v):r+(va-v)+n]
    return b''
TEXT=[s for s in secs if s[0]=='.text'][0];T0,T1=TEXT[1],TEXT[1]+TEXT[3];TRAW=TEXT[2]
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
va=0x47C620
print("=== gate fn refs to esp+0x1c / ebp+8 in 47C620..47CB20 ===")
while va<0x47CB20:
    got=list(md.disasm(rd(va,16),va,count=1))
    if not got: va+=1;continue
    i=got[0]
    if '0x1c' in i.op_str and 'esp' in i.op_str: print("  %08X %-7s %s"%(i.address,i.mnemonic,i.op_str))
    va+=i.size
print("=== direct E8 callers of 47C620 ===")
for va in range(T0,T1-4):
    if data[TRAW+(va-T0)]==0xE8:
        rel=int.from_bytes(data[TRAW+(va+1-T0):TRAW+(va+5-T0)],'little',signed=True)
        if (va+5+rel)&0xFFFFFFFF==0x47C620: print("  call@%08X"%va)
