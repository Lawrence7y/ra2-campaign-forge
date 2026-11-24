#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump caller alternate path 0x43F5EF..0x43F6C0 fully. READ-ONLY skipdata=True."""
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
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
def dis(va,n):
    for i in md.disasm(read(va,n),va): yield i
def fmt(i): return "%08X  %-8s %s"%(i.address,i.mnemonic,i.op_str)

print("=== caller alternate path 0x43F5EF .. 0x43F6C0 ===")
calls=[]
for i in dis(0x43F5EF,0x43F6C0-0x43F5EF):
    try: ops=i.operands
    except Exception: continue
    s=fmt(i)
    if i.mnemonic in ('call','jmp') and ops and ops[0].type==X86_OP_IMM:
        s+="  ;->%08X"%ops[0].imm
        if i.mnemonic=='call': calls.append((i.address,ops[0].imm))
    print(" ",s)
print("CALLS:",[(hex(a),hex(b)) for a,b in calls])
print("gate 0x47C620 called?", any(b==0x47C620 for a,b in calls))
