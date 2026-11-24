#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump caller 0x43F180 reject branch targets + check TerrainClass/ThingClass +0x14 bit0.
READ-ONLY. capstone skipdata=True."""
import struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG
BIN=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"; IB=0x400000
pe=pefile.PE(BIN,fast_load=True); pe.parse_data_directories()
SEC=[(s.Name.rstrip(b'\0').decode('latin-1'),IB+s.VirtualAddress,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
DATA=open(BIN,'rb').read()
def va2off(va):
    for n,sva,vsz,praw,rsz in SEC:
        if sva<=va<sva+max(vsz,rsz):
            o=praw+(va-sva)
            if 0<=o<len(DATA): return o
    return None
def read(va,n):
    o=va2off(va); return DATA[o:o+n] if o is not None else b'\0'*n
def u32(va): return struct.unpack('<I',read(va,4))[0]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
def dis(va,n):
    for i in md.disasm(read(va,n),va): yield i
def fmt(i): return "%08X  %-8s %s"%(i.address,i.mnemonic,i.op_str)

def dump(va, maxb, label):
    print("="*66); print(label, hex(va)); print("="*66)
    for i in dis(va,maxb):
        try: ops=i.operands
        except Exception: continue
        s=fmt(i)
        if i.mnemonic in ('call','jmp') and ops and ops[0].type==X86_OP_IMM:
            s+="  ;->%08X"%ops[0].imm
        print(" ",s)
        if i.mnemonic=='ret': break

for a,lbl in [(0x43F504,'caller reject 0x43F504 (gate al=0 -> je)'),
              (0x43F5D8,'caller reject 0x43F5D8 (canplace nonzero)'),
              (0x43F5E0,'caller reject 0x43F5E0 (base slot73 al=0)'),
              (0x43F5EF,'caller branch 0x43F5EF (BType+E58==0)')]:
    dump(a,0x40,lbl)

# TerrainClass: find RTTI-named constructor and scan +0x14 writes in first 0x400 bytes.
# Known from R14 atlas: search all .text for 'mov byte [reg+0x14], imm' with odd/even values
# grouped by function is expensive; instead check WhatAmI constants referenced near terrain.
print("="*66); print("WhatAmI compare constants in 0x47C620:", [6,0x24,2]); print("="*66)
