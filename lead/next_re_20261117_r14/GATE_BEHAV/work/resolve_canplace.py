#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolve caller can-place virtual [esi+0x1AC] at 0x43F218 and the 0x6F4A70
base slot-73 call at 0x43F198. READ-ONLY. capstone skipdata=True."""
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

# BuildingClass main vtable (R14) = 0x7E3EBC ; slot at +0x1AC
vt=0x7E3EBC
target=u32(vt+0x1AC)
print("BuildingClass vt=%08X  [vt+0x1AC]=%08X"%(vt,target))
print("  -> vtable slot index (0x1AC/4) = %d"%(0x1AC//4))

def dump_fn(va, maxb=0x600, label=""):
    print("="*70); print(label, "entry", hex(va)); print("="*70)
    ncall=0
    for i in dis(va,maxb):
        try: ops=i.operands
        except Exception: print("  DATA",i.bytes.hex(' ')); continue
        line=fmt(i)
        if i.mnemonic in ('call','jmp') and ops and ops[0].type==X86_OP_IMM:
            line+="   ; -> %08X"%ops[0].imm; ncall+=1
        # annotate absolute global reads
        for o in ops:
            if o.type==X86_OP_MEM and o.mem.base==0 and o.mem.index==0:
                line+="   ; GLOB %08X"%(o.mem.disp & 0xffffffff)
        print(" ",line)
        if i.mnemonic=='ret': break
    print("  (call/jmp imm count until first ret:",ncall,")")

if 0x400000<=target<0x500000:
    dump_fn(target, 0x800, "can-place virtual target")

# Also check other candidate vtables that may hold this building object's vt
for cand in (0x7E3EBC,0x7E3F00,0x7E3E00):
    t=u32(cand+0x1AC)
    print("cand vt %08X -> [+0x1AC]=%08X"%(cand,t))
