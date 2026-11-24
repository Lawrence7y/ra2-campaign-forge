#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T2b: disassemble the 5 'setg' selector callsites of 0x47C3D0 and key callees."""
import sys, struct
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_GATE_B\work')
import peutil
from peutil import *

def is_data(i): return i.id==0 or i.mnemonic.startswith('.')

SETG_SITES=[0x4B2BCD,0x4B30B2,0x516A41,0x6A221D,0x6A2702]
for site in SETG_SITES:
    print("="*70)
    print("setg site call 0x47C3D0 @ 0x%08X (window -28..+8)"%site)
    for insn in disasm(site-28, 40, skipdata=True):
        if is_data(insn): continue
        print("  "+fmt_insn(insn))

print()
print("="*70)
print("Key callee 0x578540 (called from 0x47C880)")
for insn in disasm(0x578540, 0x120, skipdata=True):
    if is_data(insn): continue
    print("  "+fmt_insn(insn))
    if insn.mnemonic.startswith('ret'): break

print()
print("="*70)
print("Key callee 0x568300 (called from 0x47C6B6)")
for insn in disasm(0x568300, 0x120, skipdata=True):
    if is_data(insn): continue
    print("  "+fmt_insn(insn))
    if insn.mnemonic.startswith('ret'): break
