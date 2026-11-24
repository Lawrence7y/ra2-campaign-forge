#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Identify classes of constructor functions via RTTI, and trace bit0-set chain.
RTTI chain: vtable VA -> [vt-4]=COL -> [COL+0xC]=TD -> TD+8 inline ASCII name.
COL is at vt-4 (NOT vt-8). TD+8 is an INLINE string, not a pointer (tech 7).
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
import peutil as P
from capstone.x86 import X86_OP_IMM, X86_OP_REG, X86_OP_MEM

outdir = os.path.join(os.path.dirname(__file__), '..', 'EVIDENCE')
os.makedirs(outdir, exist_ok=True)
L = []

def get_ops(insn):
    try: return insn.operands
    except Exception: return []

def rtti_name_of_vtable(vt):
    """Given a vtable VA (first virtual method slot), read COL=vt-4, TD=[COL+0xC], name=TD+8."""
    col = P.u32(vt - 4)
    td = P.u32(col + 0xC)
    # TD+8 is inline name string; read until non-printable
    b = P.read(td + 8, 80)
    name = b.split(b'\x00')[0]
    try: s = name.decode('ascii')
    except Exception: s = repr(name)
    return col, td, s

def find_vptr_writes(fn_va, size):
    """Return list of (site, reg_mem_repr, imm) for mov [reg+off],imm where imm is a vtable in .rdata
       that has a valid COL/name (or raw)."""
    out = []
    insns = list(P.disasm(fn_va, size))
    for insn in insns:
        ops = get_ops(insn)
        if len(ops) == 2 and ops[0].type == X86_OP_MEM and ops[1].type == X86_OP_IMM:
            imm = ops[1].imm
            sec = P.section_of(imm)
            if sec and sec[0] == '.rdata':
                out.append((insn.address, P.fmt(insn), imm))
    return out, insns

def find_direct_callers(target, text_sva=0x401000, text_end=0x7E1000):
    code = P.read(text_sva, text_end-text_sva)
    callers = []
    for i in range(len(code)-5):
        if code[i] == 0xE8:
            rel = struct.unpack('<i', code[i+1:i+5])[0]
            if text_sva + i + 5 + rel == target:
                site = text_sva+i
                first = next(P.disasm(site, 8), None)
                if first and first.mnemonic=='call' and P.imm_target(first)==target:
                    callers.append(site)
    return callers

atlas_path = r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
import csv
rows = list(csv.DictReader(open(atlas_path, encoding='utf-8'), delimiter='\t'))
def containing(addr):
    for r in rows:
        e=int(r['entry'],16); s=int(r['size'])
        if e<=addr<e+s: return e,s
    return None,None

# Functions to inspect: bit0-setter, its two callers, Inf ctor, and the base ctor
FNS = [
    (0x6F2B40, 0x1833, 'bit0-setter host'),
    (0x4D31E0, 0x35C, 'base ctor called by InfCtor'),
    (0x43B740, 0x5B0, 'caller of bit0-setter #2'),
    (0x517A50, 0x269, 'InfantryClass ctor'),
]
for va, sz, label in FNS:
    L.append("\n=== %s @ %08X size %X ===" % (label, va, sz))
    wr, insns = find_vptr_writes(va, sz)
    L.append("vptr-like writes (imm in .rdata):")
    for site, txt, imm in wr:
        try:
            col, td, name = rtti_name_of_vtable(imm)
            L.append("  %s ; COL=%08X TD=%08X name=%s" % (txt, col, td, name))
        except Exception as e:
            L.append("  %s ; imm=%08X (rtti read err %s)" % (txt, imm, e))
    # bit0 checks
    L.append("bit0 ops:")
    for insn in insns:
        s = insn.mnemonic+' '+insn.op_str
        if 'al, 1' in s or ('0x14' in s and insn.mnemonic in ('mov','or','and','test')):
            L.append("  "+P.fmt(insn))

# callers of 4D31E0, 43B740, 517A50
for tgt in [0x4D31EA-1, 0x4D31E0, 0x43B740]:
    pass
for tgt,label in [(0x4D31E0,'4D31E0'),(0x43B740,'43B740')]:
    cs = find_direct_callers(tgt)
    L.append("\ndirect callers of %s: %s" % (label, ' '.join('%08X'%c for c in cs)))
    for c in cs:
        e,s = containing(c)
        L.append("  site %08X in fn %s" % (c, ('%08X size %X'%(e,s)) if e is not None else 'NOT_IN_ATLAS'))

with open(os.path.join(outdir,'ctor_rtti_chain.txt'),'w',encoding='utf-8') as f:
    f.write("\n".join(L)+"\n")
print("wrote ctor_rtti_chain.txt")
print("\n".join(L))
