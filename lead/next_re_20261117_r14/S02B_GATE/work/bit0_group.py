#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Group all 'mov [reg+0x14], imm-odd' write points by their containing function;
   check whether any fall in the three unit-class ctors. Emit full list to EVIDENCE."""
import sys, os, csv
sys.path.insert(0, os.path.dirname(__file__))
import peutil as P
from capstone.x86 import X86_OP_IMM, X86_OP_MEM

outdir=os.path.join(os.path.dirname(__file__),'..','EVIDENCE')
L=[]
def opv(insn):
    try: return insn.operands
    except Exception: return []
def plus14(op):
    return op.type==X86_OP_MEM and getattr(op.mem,'disp',None)==0x14

rows=list(csv.DictReader(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv',encoding='utf-8'),delimiter='\t'))
def containing(addr):
    for r in rows:
        e=int(r['entry'],16); s=int(r['size'])
        if e<=addr<e+s: return e
    return None

odd=[]
for insn in P.disasm(0x401000,0x7E1000-0x401000):
    ops=opv(insn)
    if insn.mnemonic=='mov' and len(ops)==2 and plus14(ops[0]) and ops[1].type==X86_OP_IMM and (ops[1].imm&1)==1:
        odd.append((insn.address,ops[1].imm))
L.append("all mov [reg+0x14], imm-odd count=%d"%len(odd))
for a,imm in odd:
    e=containing(a)
    tag=''
    if e==0x517A50: tag=' INFANTRY-CTOR'
    elif e==0x413D20: tag=' AIRCRAFT-CTOR'
    elif e==0x7353C0: tag=' UNIT-CTOR'
    elif e==0x6F2B40: tag=' TECHNO-CTOR'
    L.append("  %08X imm=%02X fn=%s%s"%(a,imm&0xff,('%08X'%e) if e else 'NOT_IN_ATLAS',tag))
with open(os.path.join(outdir,'bit0_imm_odd_grouped.txt'),'w',encoding='utf-8') as f:
    f.write("\n".join(L)+"\n")
print(L[0])
for line in L:
    if 'CTOR' in line: print(line)
print("in 3 unit ctors:", sum(1 for a,i in odd if containing(a) in (0x517A50,0x413D20,0x7353C0)))
