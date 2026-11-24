#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Global scan: all write points that set bit0=1 of [reg+0x14].
Patterns:
  A) or r8,1 (or mov r8,1 / add r8,1) then mov byte [reg+0x14], r8 within a few insns
  B) mov byte [reg+0x14], imm where imm & 1 == 1
Also dump control-flow region around 0x6F322F and FootClass RMW 0x4D34DA.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import peutil as P
from capstone.x86 import X86_OP_IMM, X86_OP_REG, X86_OP_MEM

outdir=os.path.join(os.path.dirname(__file__),'..','EVIDENCE')
L=[]
def go(insn):
    try: return insn.operands
    except Exception: return []

# --- A/B global scan over whole .text ---
text_sva=0x401000; text_end=0x7E1000
insns=list(P.disasm(text_sva, text_end-text_sva))
L.append("total .text insns (skipdata=True): %d"%len(insns))

# Build index: for each instruction, record writes to [reg+0x14]
# helper: detect mem operand base register + disp 0x14
def is_plus14_mem(op):
    if op.type!=X86_OP_MEM: return False
    # X86Op.mem.disp holds displacement; guard with getattr for safety
    return getattr(op.mem,'disp',None)==0x14

writes_plus14=[]
for i,insn in enumerate(insns):
    ops=go(insn)
    if insn.mnemonic=='mov' and len(ops)==2 and is_plus14_mem(ops[0]):
        src=ops[1]
        writes_plus14.append((i,insn,src))

L.append("all 'mov [reg+0x14], src' count: %d"%len(writes_plus14))
L.append("\n=== writes to [reg+0x14] with src=IMM odd (bit0=1) ===")
n_imm_odd=0
for i,insn,src in writes_plus14:
    if src.type==X86_OP_IMM and (src.imm & 1)==1:
        L.append("  "+P.fmt(insn)); n_imm_odd+=1
L.append("count imm-odd: %d"%n_imm_odd)

L.append("\n=== writes to [reg+0x14], reg8 where reg8 was OR'd with 1 shortly before ===")
# find or reg8,1 instructions
or1_idx=[]
for i,insn in enumerate(insns):
    ops=go(insn)
    if insn.mnemonic in ('or','add') and len(ops)==2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_IMM and ops[1].imm==1:
        or1_idx.append(i)
for i,insn,src in writes_plus14:
    if src.type!=X86_OP_REG: continue
    # look back up to 8 insns for 'or <same reg>,1'
    for j in range(max(0,i-8),i):
        jins=insns[j]; jops=go(jins)
        if jins.mnemonic=='or' and len(jops)==2 and jops[0].type==X86_OP_REG and jops[0].reg==src.reg and jops[1].type==X86_OP_IMM and jops[1].imm==1:
            L.append("  OR@%08X -> WRITE %s"%(jins.address,P.fmt(insn)))
            break

# --- Control-flow region around 0x6F322F ---
L.append("\n=== region 0x6F31E0..0x6F3260 (around bit0-set in TechnoClass ctor) ===")
for insn in P.disasm(0x6F31E0,0x80):
    L.append("  "+P.fmt(insn))

L.append("\n=== FootClass ctor RMW region 0x4D34C0..0x4D34F0 ===")
for insn in P.disasm(0x4D34C0,0x40):
    L.append("  "+P.fmt(insn))

with open(os.path.join(outdir,'bit0_write_points_global.txt'),'w',encoding='utf-8') as f:
    f.write("\n".join(L)+"\n")
print("wrote bit0_write_points_global.txt")
# console summary
for line in L:
    if line.startswith('total') or line.startswith('all ') or line.startswith('count') or 'OR@' in line or 'imm-odd' in line or '0x6F3228' in line or '0x6F322F' in line or '0x6F3237' in line or '0x4D34DA' in line or '0x4D34E0' in line:
        print(line)
