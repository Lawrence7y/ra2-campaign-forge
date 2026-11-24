#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolve handler call targets against coverage names; dump handler disasm."""
import sys, csv
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S15-K3\work")
import pehelp as p
from capstone.x86 import X86_OP_IMM

COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
names={}
with open(COV,encoding='utf-8-sig') as f:
    for r in csv.DictReader(f,delimiter='\t'):
        names[(r['entry'] or '').strip().lower()]=(r['name'],r['grade'],r['subsystem'],r['one_line_semantics'])

def resolve(va):
    key=f"{va:08x}"
    if key in names:
        nm,gr,sub,sem=names[key]
        return f"{nm} [{gr}] {sub}"
    return "(unnamed/not-in-coverage)"

HANDLERS = {
 'ACT10(ID10)': 0x6DE72F,
 'ACT99(ID99)': 0x6DE845,
 'ACT105(ID105)': 0x6DF588,
 'ACT112(ID112)': 0x6DF795,
 'ACT27(ID27)': 0x6DE5C9,
 'ACT103(ID103)': 0x6DE66A,
 'ACT23(ID23)': 0x6DE418,
}
for label,h in HANDLERS.items():
    print("="*90)
    print(f"{label} handler @ 0x{h:08X}")
    print("="*90)
    for insn in p.disasm(h, 0x180):
        txt=p.fmt(insn)
        if insn.mnemonic=='call' and insn.operands and insn.operands[0].type==X86_OP_IMM:
            t=insn.operands[0].imm
            txt += "   ; -> "+resolve(t)
        print(txt)
    print()
