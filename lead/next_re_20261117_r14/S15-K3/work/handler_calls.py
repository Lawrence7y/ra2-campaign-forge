#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S15-K3\work")
import pehelp as p
from capstone.x86 import X86_OP_IMM

CAND = {
0x006D0F00,0x006D6070,0x006E1830,0x006E2A10,0x006E2AA0,0x006E4790,
0x006E47C0,0x006E6310,0x006EA3E0,0x006F1920,0x0070F120,0x0071FA30,
0x00721270,0x00726910,0x00727AA0,0x0072DDB0,0x0072DEF0,0x00751590,
0x00752460,0x00763610,0x00763690,
}

def handler_calls(va, maxbytes=0x120):
    """disassemble one handler block; stop at first ret/jmp; collect direct call imm targets"""
    out=[]
    for insn in p.disasm(va, maxbytes):
        if insn.mnemonic.startswith('ret'):
            break
        if insn.mnemonic == 'jmp' and insn.op_str.startswith('0x'):
            # unconditional tail jmp - record but keep scanning a bit
            pass
        if insn.mnemonic == 'call' and insn.operands and insn.operands[0].type == X86_OP_IMM:
            out.append((insn.address, insn.operands[0].imm))
    return out

# ACTION handlers
print("=== ACTION handler blocks -> direct call targets (only blocks hitting a candidate) ===")
for i in range(145):
    h = p.dword_va(0x6DFDEC + 4*i)
    calls = handler_calls(h)
    hits = [(a,t) for a,t in calls if t in CAND]
    if hits:
        allt = ' '.join(f"{t:08X}" for a,t in calls)
        print(f"ACT ID {i+1:3d} handler 0x{h:08X}: calls=[{allt}]  <== CAND {[f'{t:08X}' for a,t in hits]}")

print()
print("=== EVENT L1 handler blocks -> direct call targets ===")
for i in range(12):
    h = p.dword_va(0x71F218 + 4*i)
    calls = handler_calls(h)
    hits = [(a,t) for a,t in calls if t in CAND]
    allt = ' '.join(f"{t:08X}" for a,t in calls)
    mark = f"  <== CAND {[f'{t:08X}' for a,t in hits]}" if hits else ""
    print(f"L1[{i:2d}] handler 0x{h:08X}: calls=[{allt}]{mark}")

print()
print("=== per-candidate: which action/event handlers call it ===")
for c in sorted(CAND):
    srcs=[]
    for i in range(145):
        h = p.dword_va(0x6DFDEC + 4*i)
        for a,t in handler_calls(h):
            if t==c:
                srcs.append(f"ACT{i+1}@0x{a:X}")
    for i in range(12):
        h = p.dword_va(0x71F218 + 4*i)
        for a,t in handler_calls(h):
            if t==c:
                srcs.append(f"L1[{i}]@0x{a:X}")
    print(f"0x{c:08X}: {srcs}")
