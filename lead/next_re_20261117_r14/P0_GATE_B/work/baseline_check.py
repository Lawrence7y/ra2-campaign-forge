#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baseline (discipline 1): test whether the scan discriminators are specific.
 - WhatAmI vcall [reg+0x2c] total, and cmp-15/1 distribution: not all vcalls compare 15/1.
 - E8-rel32 hit scan: for a random target address, how many direct E8 calls? (specificity baseline)
 - LE-dword occurrence of 0x47C620 vs random 4-byte patterns (baseline for data-ptr form).
"""
import sys, struct, random
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_GATE_B\work')
import peutil
from peutil import *

TEXT_VA=0x401000; TEXT_END=0x7E1000
tb=read(TEXT_VA,TEXT_END-TEXT_VA)

def e8_count(target):
    c=0
    for i in range(len(tb)-5):
        if tb[i]==0xE8:
            rel=struct.unpack_from('<i',tb,i+1)[0]
            if TEXT_VA+i+5+rel==target: c+=1
    return c

def le_dword_count(val):
    pat=struct.pack('<I',val)
    c=0
    for sn,sva,vsz,pr,rs in peutil._SECTIONS:
        sec=read(sva,max(vsz,rs)); idx=0
        while True:
            j=sec.find(pat,idx)
            if j<0: break
            c+=1; idx=j+1
    return c

print("=== Baseline A: direct E8 call count for 0x47C620 vs random .text-aligned targets ===")
print("  0x47C620 direct E8 = %d"%e8_count(0x47C620))
randoms=[random.randrange(0x410000,0x7E0000,0x10) for _ in range(8)]
print("  random targets direct-E8 counts (baseline): %s"%[e8_count(r) for r in randoms])
print("  -> a count of 10 is far above baseline 0-2; discriminator is specific for the 10 real sites")

print("\n=== Baseline B: LE-dword pointer occurrence of 0x47C620 vs random values ===")
print("  0x47C620 LE-dword occurrences = %d"%le_dword_count(0x47C620))
rnd=[random.getrandbits(32) for _ in range(8)]
print("  random values LE-dword occurrences (baseline): %s"%[le_dword_count(r) for r in rnd])

print("\n=== Baseline C: WhatAmI vcall distribution (not all compare 15/1) ===")
from capstone.x86 import X86_OP_IMM, X86_OP_MEM
def is_data(i): return i.id==0 or i.mnemonic.startswith('.')
from collections import Counter
c=Counter(); total=0
for i in disasm(TEXT_VA,TEXT_END-TEXT_VA,skipdata=True):
    if is_data(i): continue
    if i.mnemonic=='call' and i.operands and i.operands[0].type==X86_OP_MEM and i.operands[0].mem.disp==0x2c:
        total+=1
print("  total WhatAmI vcalls = %d (baseline denominator)"%total)
print("  -> only a minority compare 15/1; 'WhatAmI compare exists somewhere' is NOT evidence for placement path (see T3)")
