#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Identify 0x413D20, 0x7353C0 via RTTI; scan all three unit-class ctors
   for the or-al-1 -> mov [reg+0x14],al bit0-set pattern and the call chain into 0x6F2B40.
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
import peutil as P
from capstone.x86 import X86_OP_IMM, X86_OP_REG, X86_OP_MEM

outdir = os.path.join(os.path.dirname(__file__), '..', 'EVIDENCE')
L=[]
def get_ops(insn):
    try: return insn.operands
    except Exception: return []
def rtti(vt):
    col=P.u32(vt-4); td=P.u32(col+0xC)
    b=P.read(td+8,80).split(b'\x00')[0]
    try: s=b.decode('ascii')
    except: s=repr(b)
    return col,td,s

# atlas sizes for candidate ctors
import csv
rows=list(csv.DictReader(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv',encoding='utf-8'),delimiter='\t'))
def size_of(e):
    for r in rows:
        if int(r['entry'],16)==e: return int(r['size'])
    return 0x400

CAND=[(0x413D20,'candidate A'),(0x7353C0,'candidate B'),(0x517A50,'InfantryClass ctor')]
for va,label in CAND:
    sz=size_of(va)
    L.append("\n=== %s @ %08X size %X ==="%(label,va,sz))
    insns=list(P.disasm(va,sz))
    for insn in insns:
        ops=get_ops(insn)
        # vptr writes to rdata with RTTI
        if len(ops)==2 and ops[0].type==X86_OP_MEM and ops[1].type==X86_OP_IMM:
            imm=ops[1].imm; sec=P.section_of(imm)
            if sec and sec[0]=='.rdata':
                col,td,s=rtti(imm)
                if s.startswith('.?AV'):
                    L.append("  VPTR %s ; COL=%08X TD=%08X %s"%(P.fmt(insn),col,td,s))
        # calls to 4D31E0 (FootCtor) / 6F2B40 (TechnoCtor)
        if insn.mnemonic=='call':
            t=P.imm_target(insn)
            if t in (0x4D31E0,0x6F2B40):
                L.append("  CALL %s ; -> %08X"%(P.fmt(insn),t))
        # bit0 ops
        s=insn.mnemonic+' '+insn.op_str
        if ('0x14' in s and insn.mnemonic in ('mov','or','and','test')) or 'al, 1' in s:
            L.append("  BIT0 %s"%P.fmt(insn))

with open(os.path.join(outdir,'unit_class_ctors.txt'),'w',encoding='utf-8') as f:
    f.write("\n".join(L)+"\n")
print("\n".join(L))
