#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T3: byte-level re-verification of 5 sampled [已证] S15 rows (independent of atlas-derived claims)."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S15-K3\work")
import pehelp as p
from capstone.x86 import X86_OP_IMM

print("### T3-A: GetSize @0x6E4630 / WhatAmI @0x6E4640 — B8 imm32 C3 constants")
for va in (0x6E4630,0x6E4640):
    print(f"0x{va:08X}: {p.read_va(va,8).hex()}  -> " + ' | '.join(p.fmt(i) for i in p.disasm(va,8)))
print()

print("### T3-B: HasOccured @0x71E940 dispatch insn + L1/L2 (already checked, re-read)")
print(p.fmt(list(p.disasm(0x71E964,6))[0]))
print("L1[0..3]:", [hex(p.dword_va(0x71F218+4*i)) for i in range(4)])
print("L2[0..16]:", [p.byte_va(0x71F248+i) for i in range(17)])
print()

print("### T3-C: WakeupSelf @0x6E01C0 — check Execute handler ACT81 (0x6DEBD0) unique call")
h=0x6DEBD0
calls=[]
for insn in p.disasm(h,0x60):
    if insn.mnemonic=='call' and insn.operands and insn.operands[0].type==X86_OP_IMM:
        calls.append(insn.operands[0].imm)
print(f"ACT81 handler 0x{h:08X} direct calls: {[hex(x) for x in calls]}")
print(f"0x6E01C0 body first 8B: {p.read_va(0x6E01C0,8).hex()}")
print()

print("### T3-D: TagClass::TagClass @0x6E4DE0 — entry writes vptr chain + base ctor call")
for insn in p.disasm(0x6E4DE0,0x60):
    print(p.fmt(insn))
print()

print("### T3-E: PlayMusicTheme @0x720B20 — dispatch ID20 handler ACT20=0x6DE8E4, string push 0x465d80")
h=0x6DE8E4
for insn in p.disasm(h,0x30):
    print(p.fmt(insn))
print("string @0x465d80:", p.read_va(0x465d80,48).split(b'\x00')[0])
