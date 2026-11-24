#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, csv
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S15-K3\work")
import pehelp as p
from capstone.x86 import X86_OP_IMM

ATL = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
sizes={}
with open(ATL,encoding='utf-8-sig') as f:
    for r in csv.DictReader(f,delimiter='\t'):
        sizes[(r['entry'] or '').strip().lower()]=r

CAND = [0x006D6070,0x006E1830,0x0070F120,0x0072DDB0,0x0072DEF0,
        0x006D0F00,0x006E4790,0x006E47C0]

for c in CAND:
    key=f"{c:08x}"
    row=sizes.get(key,{})
    sz=int(row.get('size','0') or 0)
    ninst=int(row.get('n_instr','0') or 0)
    ncallers=int(row.get('n_callers','0') or 0)
    print("="*90)
    print(f"CANDIDATE 0x{c:08X}  atlas size={sz} n_instr={ninst} n_callers={ncallers}")
    print("="*90)
    # disassemble full function (cap the size); also show call targets
    code_sz = sz if sz>0 else 0x120
    calls=[]
    for insn in p.disasm(c, code_sz):
        txt=p.fmt(insn)
        if insn.mnemonic=='call' and insn.operands and insn.operands[0].type==X86_OP_IMM:
            calls.append(insn.operands[0].imm)
            txt += "   ; CALL -> 0x%08X"%insn.operands[0].imm
        print(txt)
    print(f"-- direct call targets: {[hex(x) for x in calls]}")
    print()
