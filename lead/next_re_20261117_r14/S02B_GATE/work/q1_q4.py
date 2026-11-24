#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q1 caller context, Q4 globals byte evidence, RTTI chain verify, WhatAmI set."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
import peutil as P
from capstone.x86 import X86_OP_IMM, X86_OP_REG, X86_OP_MEM

outdir=os.path.join(os.path.dirname(__file__),'..','EVIDENCE')
L=[]
def go(insn):
    try: return insn.operands
    except Exception: return []

# --- RTTI verify BuildingTypeClass chain (arg2) ---
L.append("=== RTTI verify: BuildingTypeClass (arg2 of 0x47C620) ===")
for col,td,label in [(0x7FC618,0x8193A8,'BuildingTypeClass'),(0x824500,None,'HouseClass control')]:
    if td is None:
        td=P.u32(col+0xC)
    name=P.read(td+8,60).split(b'\x00')[0]
    L.append("COL=%08X TD=%08X name=%s  (COL+0xC readback=%08X)"%(col,td,name,P.u32(col+0xC)))
# also check: what vtable's COL is 0x7FC618? scan .rdata for dword==0x7FC618 (COL stored at vt-4)
L.append("-- .rdata locations holding 0x7FC618 (COL) -> vtable=loc+4 --")
# scan raw .data/.rdata for little-endian 0x7FC618
for (name,sva,vsz,praw,rsz) in P._SECTIONS:
    if name not in ('.rdata','.data'): continue
    blob=P.read(sva, max(vsz,rsz))
    needle=struct.pack('<I',0x7FC618)
    start=0
    while True:
        k=blob.find(needle,start)
        if k<0: break
        L.append("  %s %08X holds COL -> vtable %08X"%(name,sva+k,sva+k+4))
        start=k+1

# --- Q4 globals: scan whole .text for writes/reads of 0xA8E7AC, 0xA8E9A0, 0xA8ED6B ---
L.append("\n=== Q4 global access forms (whole .text, instruction-boundary) ===")
for gl in (0xA8E7AC,0xA8E9A0,0xA8ED6B):
    L.append("-- global %08X --"%gl)
    cnt=0
    for insn in P.disasm(0x401000,0x7E1000-0x401000):
        ops=go(insn)
        s=insn.mnemonic+' '+insn.op_str
        # absolute addressing [0x........]
        hit=False
        for op in ops:
            if op.type==X86_OP_MEM and op.mem.base==0 and op.mem.index==0 and op.mem.disp==gl:
                hit=True
        if hit:
            L.append("  "+P.fmt(insn)); cnt+=1
    L.append("  total abs-form accesses: %d"%cnt)

# --- Q1: fresh dump 0x43F180 mode-1/3 path around call 0x47C620 ---
L.append("\n=== Q1: 0x43F180 call-to-gate context (fresh) 0x43F280..0x43F2C0 ===")
for insn in P.disasm(0x43F280,0x50):
    L.append("  "+P.fmt(insn))

# --- WhatAmI comparison set in 47C620: call [vt+0x2c] followed by cmp eax,imm ---
L.append("\n=== WhatAmI (call [vt+0x2c]) comparisons in 0x47C620 ===")
insns=list(P.disasm(0x47C620,0x4A0))
for i,insn in enumerate(insns):
    ops=go(insn)
    if insn.mnemonic=='call' and len(ops)==1 and ops[0].type==X86_OP_MEM and ops[0].mem.disp==0x2c:
        # next insn cmp eax,imm
        if i+1<len(insns):
            n=insns[i+1]; nops=go(n)
            if n.mnemonic=='cmp' and len(nops)==2 and nops[0].type==X86_OP_REG and nops[1].type==X86_OP_IMM:
                L.append("  %s ; %s -> WhatAmI==%d"%(P.fmt(insn),P.fmt(n),nops[1].imm))

with open(os.path.join(outdir,'q1_q4_evidence.txt'),'w',encoding='utf-8') as f:
    f.write("\n".join(L)+"\n")
print("wrote q1_q4_evidence.txt")
for line in L:
    if ('name=' in line and 'COL=' in line) or 'holds COL' in line or 'total abs-form' in line or 'WhatAmI==' in line or 'global ' in line:
        print(line)
