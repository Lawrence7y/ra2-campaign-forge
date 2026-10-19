#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\tools")
from re_gap_spysat_deep import read_bytes, md, base, names, secs

text = next(s for s in secs if s['name'] == '.text')
code = text['raw'][:text['vsize']]
tva = text['va']

print("=== CALLS TO 0x487150, 0x487160, 0x487170, 0x487180, 0x487690 ===")
call_targets = {
    0x00487150: "Cell::inc_7C",
    0x00487160: "Cell::dec_7C",
    0x00487170: "Cell::inc_AC",
    0x00487180: "Cell::dec_AC",
    0x00487690: "Cell::sub_487690",
    0x00487950: "Cell::IsShrouded",
    0x00586360: "MapClass::IsCellShrouded",
    0x005865E0: "MapClass::IsCoordShrouded",
    0x004555D0: "IsGeneratingGap",
    0x004556D0: "CreateGap_Super",
    0x00455820: "CreateGap_Main",
    0x00455980: "DestroyGap_Aux",
    0x00455A80: "DestroyGap_Main"
}

pos = 0
import capstone as _cs

found_calls = []
while pos < len(code):
    for insn in md.disasm(code[pos:], tva + pos):
        if insn.mnemonic in ('call', 'jmp'):
            for op in insn.operands:
                if op.type == _cs.x86.X86_OP_IMM:
                    target = op.imm & 0xFFFFFFFF
                    if target in call_targets:
                        found_calls.append((insn.address, insn.mnemonic, target, call_targets[target]))
        pos = insn.address - tva + insn.size
    if pos < len(code):
        pos += 1

for addr, mnem, tgt, tname in found_calls:
    print(f"  0x{addr:08X}: {mnem:<4} 0x{tgt:08X} ({tname})")

print("\n=== CALLS TO VTABLE SLOTS (0x350, 0x4F4, 0x4F8, 0x4FC, 0x500) ===")
pos = 0
slot_calls = []
while pos < len(code):
    for insn in md.disasm(code[pos:], tva + pos):
        if insn.mnemonic in ('call', 'jmp'):
            for s in ('0x350', '0x4f4', '0x4f8', '0x4fc', '0x500'):
                if s in insn.op_str.lower():
                    slot_calls.append((insn.address, insn.mnemonic, insn.op_str))
        pos = insn.address - tva + insn.size
    if pos < len(code):
        pos += 1

for addr, mnem, op in slot_calls:
    print(f"  0x{addr:08X}: {mnem:<4} {op}")
