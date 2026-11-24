#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Query cached disassembly for patterns relevant to S12-Q2."""
import os, re, sys, json
from core_disasm import get_insns

D = get_insns()
INS = D["insns"]

def find_disp(disp_hex, width=None):
    """Find all insns with a memory operand [reg+disp] or [disp] equal to disp_hex."""
    pat = re.compile(r'\[(?:[a-z0-9]+(?:\+|\-))?0x%x(?:\+|\-)?[a-z0-9]*\]' % disp_hex, re.I)
    # Simpler: match the displacement token itself
    tokpat = re.compile(r'0x%x\b' % disp_hex, re.I)
    res = []
    for (a,s,m,o) in INS:
        if '[' in o and tokpat.search(o):
            res.append((a,s,m,o))
    return res

def find_imm(imm_hex):
    tokpat = re.compile(r'\b0x%x\b' % imm_hex, re.I)
    res = []
    for (a,s,m,o) in INS:
        if tokpat.search(o) and '[' not in o:
            res.append((a,s,m,o))
    return res

def find_call(target_hex):
    pat = re.compile(r'\bcall\s+0x%x\b' % target_hex, re.I)
    return [(a,s,m,o) for (a,s,m,o) in INS if pat.search(o) or (m=='call' and o.lower()==('0x%x'%target_hex))]

def dump(rows, maxn=200):
    for (a,s,m,o) in rows[:maxn]:
        print("%08X  %-8s %s" % (a,m,o))
    if len(rows)>maxn:
        print("... (%d more)" % (len(rows)-maxn))

def is_write(mnem, opstr):
    """Best-effort: memory operand is dest for mov/and/or/xor/add/sub/inc/dec/cmp(no)/movzx etc."""
    # dest is op0 for these, unless op0 is a register and op1 is memory (mov reg,[mem] is read)
    writes = {'mov','movzx','movsx','add','sub','and','or','xor','inc','dec','shl','shr','sar','lea','neg','not','adc','sbb','imul','xchg','bts','btr','btc','stos'}
    if mnem not in writes: return None
    op0 = opstr.split(',')[0].strip()
    return '[' in op0

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv)>1 else "all"
    if what in ("520","all"):
        rows = find_disp(0x520)
        print("=== references to disp 0x520: %d ===" % len(rows))
        for (a,s,m,o) in rows:
            w = is_write(m,o)
            print("%08X  %-8s %s  %s" % (a,m,o, "WRITE" if w else ("READ" if w is False else "?")))
    if what in ("singleton","all"):
        rows = find_imm(0x87f7e8)
        print("\n=== references to imm 0x87F7E8 (MapClass singleton candidate): %d ===" % len(rows))
        dump(rows)
    if what in ("getcell","all"):
        rows = find_call(0x5657a0)
        print("\n=== calls to 0x5657A0 (GetCell candidate): %d ===" % len(rows))
        dump(rows)
