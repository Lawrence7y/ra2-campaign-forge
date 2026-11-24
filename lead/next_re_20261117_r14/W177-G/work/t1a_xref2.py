#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Disassemble windows around raw-byte hits of 0x88095C / and check call 5657a0."""
import pefile, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB=0x400000
TARGET=0x0088095C
pe=pefile.PE(EXE,fast_load=True)
data=open(EXE,"rb").read()
md=Cs(CS_ARCH_X86,CS_MODE_32)
sec=[s for s in pe.sections if s.Name.decode('latin1').strip(chr(0))=='.text'][0]
vbase=IB+sec.VirtualAddress; raw=sec.PointerToRawData; sz=sec.Misc_VirtualSize
code=data[raw:raw+sz]
pat=struct.pack("<I",TARGET)
hits=[]; off=0
while True:
    i=code.find(pat,off)
    if i<0: break
    hits.append(vbase+i); off=i+1

def va2off(va):
    for s in pe.sections:
        va2=IB+s.VirtualAddress
        if va2<=va<va2+s.Misc_VirtualSize:
            return s.PointerToRawData+(va-va2)
    return None

for h in hits:
    print("\n===== raw hit at %08X ====="%h)
    # disassemble a window starting 0x40 bytes before, 0x40 after
    st=h-0x40; en=h+0x40
    fo=va2off(st)
    win=data[fo:fo+(en-st)]
    for ins in md.disasm(win,st):
        mark=""
        if "88095c" in ins.op_str.lower(): mark="  <<< HoverGlobal"
        if ins.mnemonic=="call" and "5657a0" in ins.op_str.lower(): mark+="  <<< CALL GetCellAt"
        print("  %08X  %-7s %s%s"%(ins.address,ins.mnemonic,ins.op_str,mark))
