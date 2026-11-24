#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S05-K2 T3: disassemble named health/weapon/mission functions and list their [this+disp] accesses."""
import pefile, os, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM
ROOT=r"D:\Project\ra2-campaign-forge"
P=os.path.join(ROOT,"ra2youli","gamemd.exe")
pe=pefile.PE(P); IB=pe.OPTIONAL_HEADER.ImageBase
SECS=[(s.Name.rstrip(b"\0").decode(),s.VirtualAddress+IB,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
SM={s[0]:s for s in SECS}; TEXT=SM[".text"]; DATA=open(P,"rb").read()
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.skipdata=True; MD.detail=True
def dis(va,n=200):
    o=TEXT[3]+(va-TEXT[1]); b=DATA[o:o+4000]
    out=[]
    for ins in MD.disasm(b,va):
        out.append(ins)
        if len(out)>=n: break
    return out
for va_s in sys.argv[1:]:
    va=int(va_s,16)
    ins=dis(va,120)
    # find [reg+disp] with reg in {esi,ecx,eax,edi,ebp} (likely this) on dword fields 0x100..0x800
    print("\n=== fn %08X  (%d insns shown) ==="%(va,len(ins)))
    for i in ins:
        disp=None; base=None
        for op in i.operands:
            if op.type==X86_OP_MEM and op.mem.disp and op.mem.index==0:
                disp=int(op.mem.disp); base=i.reg_name(op.mem.base) if op.mem.base else None
        if disp is not None and 0x100<=disp<=0x800:
            print("  %08X  %-8s %-40s ; base=%s disp=0x%X"%(i.address,i.mnemonic,i.op_str,base,disp))
