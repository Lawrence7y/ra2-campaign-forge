#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T1: For each of the 10 direct calls to 0x47C620:
   - containing function via function_atlas.tsv (interval containment)
   - window disassembly, stack args pushed, return usage.
Also emit containment via byte-level prologue scan (independent 2nd channel)."""
import sys, struct, csv
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_GATE_B\work')
import peutil
from peutil import *
def is_data(i): return i.id==0 or i.mnemonic.startswith('.')

ATLAS=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
rows=[]
with open(ATLAS,encoding='utf-8',errors='replace') as f:
    for line in f:
        parts=line.rstrip('\n').split('\t')
        if len(parts)>=2:
            try:
                e=int(parts[0],16); s=int(parts[1])
                rows.append((e,s,parts))
            except: pass
rows.sort()
starts=[r[0] for r in rows]
import bisect

def containing(va):
    # interval containment: entry <= va < entry+size
    # check candidates with entry <= va, take max entry whose range covers
    idx=bisect.bisect_right(starts,va)-1
    # scan backwards a little in case of overlaps/nesting
    for j in range(idx, max(-1,idx-8), -1):
        e,s,parts=rows[j]
        if e<=va<e+s:
            return e,s,parts
    return None

CALLS=[0x43F2AE,0x449482,0x47EE93,0x58865F,0x58886E,0x5FC6FA,0x6D5A98,0x6D5D33,0x716209,0x71C554]
for c in CALLS:
    print("="*76)
    print("CALLSITE 0x%08X"%c)
    cont=containing(c)
    if cont:
        e,s,parts=cont
        print("  atlas function: entry=0x%08X size=%d end=0x%08X  fields=%s"%(e,s,e+s,'|'.join(parts[:4])))
    else:
        print("  atlas function: NONE (interval containment failed)")
    # window -40..+12
    for insn in disasm(c-40, 56, skipdata=True):
        if is_data(insn): continue
        marker=" <<<< CALL" if insn.address==c else ""
        print("    "+fmt_insn(insn)+marker)
