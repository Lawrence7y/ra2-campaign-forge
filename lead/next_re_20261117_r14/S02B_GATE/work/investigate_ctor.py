#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Investigate 0x6F2B40 (contains 0x6F322F or al,1 / mov [esi+0x14],al):
dump full body, find direct callers, detect vptr writes, detect all bit0-set chains.
Also scan the three class constructors for the or-al-1 -> mov [reg+0x14],al pattern.
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
import peutil as P
from capstone.x86 import X86_OP_IMM, X86_OP_REG, X86_OP_MEM

outdir = os.path.join(os.path.dirname(__file__), '..', 'EVIDENCE')
os.makedirs(outdir, exist_ok=True)
L = []

FN = 0x6F2B40
SIZE = 0x1833  # from atlas
L.append("=== 0x6F2B40 full body (size %X) ===" % SIZE)
insns = list(P.disasm(FN, SIZE))
for insn in insns:
    L.append(P.fmt(insn))
# vptr writes and bit0 chains
L.append("--- vptr writes (mov [reg+off], imm where imm in .rdata) ---")
def get_ops(insn):
    try:
        return insn.operands
    except Exception:
        return []
for insn in insns:
    ops = get_ops(insn)
    if len(ops) == 2 and ops[0].type == X86_OP_MEM and ops[1].type == X86_OP_IMM:
        sec = P.section_of(ops[1].imm)
        if sec and sec[0] == '.rdata':
            L.append(P.fmt(insn) + "  ; imm in .rdata")
L.append("--- bit0-related (and al,1 / or al,1 / [reg+0x14]) ---")
for i, insn in enumerate(insns):
    s = (insn.mnemonic + ' ' + insn.op_str)
    if ('0x14' in s and ('[esi' in s or '[edi' in s or '[eax' in s or '[ecx' in s or '[edx' in s or '[ebx' in s)) or 'al, 1' in s or 'al,1' in s:
        L.append(P.fmt(insn))

# Find direct callers by scanning .text for E8 rel32 targeting FN
L.append("--- direct callers of 0x6F2B40 (E8 rel32 scan, instruction-boundary filtered) ---")
text_sva = 0x401000; text_end = 0x7E1000
# quick byte scan for E8 then verify via disasm at that spot is call with imm target
code = P.read(text_sva, text_end - text_sva)
callers = []
for i in range(len(code)-5):
    if code[i] == 0xE8:
        rel = struct.unpack('<i', code[i+1:i+5])[0]
        tgt = text_sva + i + 5 + rel
        if tgt == FN:
            site = text_sva + i
            # verify instruction boundary: disassemble from site
            first = next(P.disasm(site, 8), None)
            if first and first.mnemonic == 'call' and P.imm_target(first) == FN:
                callers.append(site)
L.append("callers=%s" % ' '.join('%08X'%c for c in callers))

with open(os.path.join(outdir, 'fn_6F2B40.txt'), 'w', encoding='utf-8') as f:
    f.write("\n".join(L) + "\n")
print("wrote fn_6F2B40.txt insns=%d callers=%d" % (len(insns), len(callers)))
print("\n".join(L[-15:]))
