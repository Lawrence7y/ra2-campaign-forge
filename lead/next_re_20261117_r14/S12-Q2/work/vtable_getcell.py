#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump BuildingClass vtable 0x7E3EBC; classify each slot target by scanning its
linear instruction window for call 0x5657A0 or Location+0x9C read."""
import struct, pefile, bisect
from core_disasm import get_insns
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe=pefile.PE(EXE,fast_load=True); BASE=pe.OPTIONAL_HEADER.ImageBase
segs=[]
for s in pe.sections:
    va=BASE+s.VirtualAddress; segs.append((va,va+s.SizeOfRawData,s.PointerToRawData,s.SizeOfRawData))
def rd32(va):
    for lo,hi,raw,sz in segs:
        if lo<=va<hi:
            with open(EXE,'rb') as f:
                f.seek(raw+(va-lo)); b=f.read(4)
            return struct.unpack('<I',b)[0] if len(b)==4 else None
    return None
D=get_insns(); INS=D['insns']; addrs=[x[0] for x in INS]
VT=0x7E3EBC
for i in range(200):
    fn=rd32(VT+i*4)
    if fn is None or fn<0x401000 or fn>0x7E1000: 
        continue
    j=bisect.bisect_left(addrs,fn)
    win=INS[j:j+60]
    calls5657=any(x[2]=='call' and '0x5657a0' in x[3] for x in win)
    reads9c=any('[ecx + 0x9c]' in x[3] or '[eax + 0x9c]' in x[3] for x in win)
    if calls5657 or reads9c:
        # find first ret
        firstret=next((hex(x[0]) for x in win if x[2].startswith('ret')),None)
        print("slot[idx=%d byte=+0x%X] fn=0x%08X GetCellAt=%s Loc9C=%s firstret=%s"%(
            i,i*4,fn,calls5657,reads9c,firstret))
