#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T1-D part: disassembly-based equivalent-form scan (skipdata-safe)."""
import sys
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_GATE_B\work')
import peutil
from peutil import *
from capstone.x86 import *
TEXT_VA = 0x401000
TEXT_END = 0x7E1000
TARGET = 0x47C620

def is_data(insn):
    return insn.id == 0 or insn.mnemonic.startswith('.')

imm_refs = []
ind_calls = []
n_real = 0
for insn in disasm(TEXT_VA, TEXT_END-TEXT_VA, skipdata=True):
    if is_data(insn):
        continue
    n_real += 1
    if insn.mnemonic in ('call','jmp') and insn.operands:
        op = insn.operands[0]
        if op.type in (X86_OP_REG, X86_OP_MEM):
            ind_calls.append(insn)
    for op in insn.operands:
        if op.type == X86_OP_IMM and (op.imm & 0xFFFFFFFF) == TARGET:
            imm_refs.append(insn)

print("real instructions decoded = %d" % n_real)
print("instructions with IMM operand == 0x%08X = %d" % (TARGET, len(imm_refs)))
for insn in imm_refs:
    print("  %08X %s %s" % (insn.address, insn.mnemonic, insn.op_str))
print("indirect call/jmp (reg/mem operand) total = %d" % len(ind_calls))

# For each indirect call, look back up to 10 real insns for a load of TARGET
by_addr = {}
for insn in disasm(TEXT_VA, TEXT_END-TEXT_VA, skipdata=True):
    if not is_data(insn):
        by_addr[insn.address] = insn
addrs = sorted(by_addr.keys())
import bisect
print()
print("--- indirect call preceded by TARGET imm load within 10 prior real insns ---")
hits = 0
for insn in ind_calls:
    idx = bisect.bisect_left(addrs, insn.address)
    window = [by_addr[a] for a in addrs[max(0,idx-10):idx]]
    for pi in window:
        if any(op.type == X86_OP_IMM and (op.imm & 0xFFFFFFFF)==TARGET for op in pi.operands):
            print("  call@%08X [%s] <- %08X %s %s" % (insn.address, insn.op_str, pi.address, pi.mnemonic, pi.op_str))
            hits += 1
print("hits = %d" % hits)

# Also: mov reg,imm TARGET followed LATER by call [reg] or call reg within 10 insns
print()
print("--- TARGET imm load followed by indirect call within 10 real insns ---")
hits2 = 0
load_addrs = [insn.address for insn in imm_refs]
for la in load_addrs:
    idx = bisect.bisect_left(addrs, la)
    window = [by_addr[a] for a in addrs[idx+1:idx+11]]
    for ci in window:
        if ci.mnemonic == 'call' and ci.operands and ci.operands[0].type in (X86_OP_REG, X86_OP_MEM):
            print("  load@%08X %s %s -> call@%08X %s" % (la, by_addr[la].mnemonic, by_addr[la].op_str, ci.address, ci.op_str))
            hits2 += 1
print("hits2 = %d" % hits2)
