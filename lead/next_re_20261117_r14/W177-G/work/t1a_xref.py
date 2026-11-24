#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static xref scan: find all instructions referencing 0x88095C (hover cell global)
and check proximity to call 0x5657A0 (GetCellAt). Read-only disk disassembly."""
import pefile, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB=0x400000
TARGET=0x0088095C
GETCELL=0x005657A0
pe=pefile.PE(EXE,fast_load=True)
data=open(EXE,"rb").read()
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
# .text
sec=[s for s in pe.sections if s.Name.decode('latin1').strip(chr(0))=='.text'][0]
vbase=IB+sec.VirtualAddress; raw=sec.PointerToRawData; sz=sec.Misc_VirtualSize
code=data[raw:raw+sz]
# Method 1: raw byte scan for absolute address little-endian (as immediate or disp32)
pat=struct.pack("<I",TARGET)
raw_hits=[]
off=0
while True:
    i=code.find(pat,off)
    if i<0: break
    raw_hits.append(vbase+i)
    off=i+1
print("raw-byte occurrences of %08X in .text: %d"%(TARGET,len(raw_hits)))
for h in raw_hits: print("  %08X"%h)
# Method 2: capstone linear disasm, collect insns whose op_str references 88095c
hits=[]
for ins in md.disasm(code,vbase):
    ops=ins.op_str.lower()
    if "88095c" in ops:
        hits.append((ins.address,ins.mnemonic,ins.op_str))
print("\ncapstone insns referencing 0x88095C: %d"%len(hits))
for a,mn,ops in hits: print("  %08X  %-7s %s"%(a,mn,ops))
# For each hit, disassemble +-0x80 window and mark any call 5657a0
for a,mn,ops in hits[:40]:
    print("\n===== window around %08X ====="%a)
    rva=a-IB
    # map VA to file offset in .text
    fo=raw+(a-vbase)
    st=max(0,fo-0x60)
    win=data[st:fo+0x60]
    startva=vbase+(st-raw)
    for ins in md.disasm(win,startva):
        mark=""
        if ins.mnemonic=="call" and "5657a0" in ins.op_str.lower(): mark=" <<< CALL GetCellAt"
        if "88095c" in ins.op_str.lower(): mark+=" <<< HoverGlobal"
        print("  %08X  %-7s %s%s"%(ins.address,ins.mnemonic,ins.op_str,mark))
