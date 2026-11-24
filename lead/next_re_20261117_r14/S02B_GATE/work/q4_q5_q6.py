#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q4: classify read/write/inc/dec of the 3 globals; Q5: caller GetCellAt context;
   Q6: slot-73 asymmetry between 0x43F180 (Building) and 0x4D3780 (Unit/Inf/Aircraft)."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
import peutil as P
from capstone.x86 import X86_OP_IMM, X86_OP_REG, X86_OP_MEM

outdir=os.path.join(os.path.dirname(__file__),'..','EVIDENCE')
L=[]
def go(insn):
    try: return insn.operands
    except Exception: return []
def mem_abs_is(op, gl):
    return op.type==X86_OP_MEM and op.mem.base==0 and op.mem.index==0 and op.mem.disp==gl

# --- Q4: global read/write classification (abs-form) ---
L.append("=== Q4: global access classification (whole .text abs-form) ===")
for gl in (0xA8E7AC,0xA8E9A0,0xA8ED6B):
    reads=[];writes=[];incs=[]
    for insn in P.disasm(0x401000,0x7E1000-0x401000):
        ops=go(insn)
        if not ops: continue
        # operand 0 could be dest (write) or source (read); operand 1 may also be mem (read)
        op0=ops[0]
        is_mem0 = op0.type==X86_OP_MEM and mem_abs_is(op0,gl)
        # any operand references gl
        any_ref = any(o.type==X86_OP_MEM and mem_abs_is(o,gl) for o in ops)
        if not any_ref: continue
        m=insn.mnemonic
        # crude write detection: insn writes memory if op0 is mem and mnemonic is a store
        store_mn = m in ('mov','inc','dec','add','sub','and','or','xor','not','shl','shr','rol','ror','movzx','movsx')
        if is_mem0 and store_mn:
            writes.append(P.fmt(insn))
        else:
            reads.append(P.fmt(insn))
        if m in ('inc','dec') and is_mem0:
            incs.append(P.fmt(insn))
    L.append("-- %08X: reads=%d writes=%d inc/dec=%d --"%(gl,len(reads),len(writes),len(incs)))
    for x in incs[:20]: L.append("   INCDEC "+x)
    for x in writes[:40]: L.append("   W "+x)

# --- Q5: caller 0x43F180 GetCellAt context (full 0x43F180..0x43F2C0) ---
L.append("\n=== Q5: 0x43F180 prologue..gate-call context (fresh) ===")
for insn in P.disasm(0x43F180,0x43F2C0-0x43F180):
    s=P.fmt(insn)
    # mark call 5657a0 (GetCellAt) and 47c620 (gate)
    if insn.mnemonic=='call':
        t=P.imm_target(insn)
        if t in (0x5657A0,0x47C620): s+="  <<< " + ('GetCellAt' if t==0x5657A0 else 'GATE')
    L.append("  "+s)

# --- Q6: slot73 asymmetry: calls to 0x47C620 in 0x43F180 vs 0x4D3780 vs 0x6F4A70 ---
L.append("\n=== Q6: slot-73 bodies: does each call 0x47C620 (per-cell gate)? ===")
for va,sz,label in [(0x43F180,2443,'BuildingClass slot73'),(0x4D3780,138,'Unit/Inf/Aircraft slot73'),(0x6F4A70,51,'TechnoClass slot73')]:
    calls=[]
    for insn in P.disasm(va,sz):
        if insn.mnemonic=='call':
            t=P.imm_target(insn)
            calls.append((insn.address,t))
    gate=[c for c in calls if c[1]==0x47C620]
    L.append("%s @%08X size=%d: total_calls=%d, calls_to_47C620=%s"%(label,va,sz,len(calls),' '.join('%08X'%a for a,t in gate) if gate else 'NONE'))

with open(os.path.join(outdir,'q4_q5_q6_evidence.txt'),'w',encoding='utf-8') as f:
    f.write("\n".join(L)+"\n")
print("wrote q4_q5_q6_evidence.txt")
for line in L:
    if line.startswith('-- ') or 'INCDEC' in line or 'calls_to' in line or 'GATE' in line or 'GetCellAt' in line:
        print(line)
