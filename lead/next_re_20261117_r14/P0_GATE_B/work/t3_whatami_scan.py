#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T3: scan whole .text for comparisons against WhatAmI 15(0xF) and 1,
   plus vcall [vptr+0x2c] results compared to 15/1. Report with containing function."""
import sys, struct, csv, bisect
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_GATE_B\work')
import peutil
from peutil import *
from capstone.x86 import *
def is_data(i): return i.id==0 or i.mnemonic.startswith('.')

ATLAS=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
rows=[]
with open(ATLAS,encoding='utf-8',errors='replace') as f:
    for line in f:
        p=line.rstrip('\n').split('\t')
        if len(p)>=2:
            try: rows.append((int(p[0],16),int(p[1])))
            except: pass
rows.sort(); starts=[r[0] for r in rows]
def containing(va):
    idx=bisect.bisect_right(starts,va)-1
    for j in range(idx,max(-1,idx-6),-1):
        e,s=rows[j]
        if e<=va<e+s: return e,s
    return None

TEXT_VA=0x401000; TEXT_END=0x7E1000
PLACE_FUNCS={0x43F180,0x47C620,0x47C3D0,0x449440,0x5657A0,
             0x5FC570,0x588570,0x588750,0x6D59D0,0x6D5C50,
             0x716150,0x71C4D0,0x47EC90}
allins=[i for i in disasm(TEXT_VA,TEXT_END-TEXT_VA,skipdata=True) if not is_data(i)]
print("real instructions: %d"%len(allins))

def cmp_imm(i,val):
    return (i.mnemonic=='cmp' and i.operands and i.operands[-1].type==X86_OP_IMM
            and (i.operands[-1].imm&0xFFFFFFFF)==val)

for val,name in [(0xF,'0xF=15 Infantry'),(1,'1=1 Unit')]:
    hits=[i for i in allins if cmp_imm(i,val)]
    print("\n=== cmp ..., %s : total=%d ==="%(name,len(hits)))
    ph=0
    for i in hits:
        c=containing(i.address); fn=c[0] if c else None
        tag=""
        if fn in PLACE_FUNCS:
            tag=" [PLACE]"; ph+=1
        print("  %08X %s -> fn=%s%s"%(i.address,i.op_str,("%08X"%fn) if fn else "NONE",tag))
    print("  in placement funcs: %d"%ph)

print("\n=== WhatAmI vcall [reg+0x2c] followed within 5 insns by cmp imm ===")
from collections import Counter
cnt=Counter(); hits15_1=[]
allarr=allins
idxmap={i.address:k for k,i in enumerate(allarr)}
vc=0
for k,i in enumerate(allarr):
    if i.mnemonic=='call' and i.operands and i.operands[0].type==X86_OP_MEM and i.operands[0].mem.disp==0x2c:
        vc+=1
        for j in allarr[k+1:k+6]:
            if j.mnemonic=='cmp' and j.operands and j.operands[-1].type==X86_OP_IMM:
                v=j.operands[-1].imm&0xFFFFFFFF
                if v in (1,2,6,0xF,0x24,7):
                    cnt[v]+=1
                    if v in (1,0xF):
                        c=containing(j.address)
                        hits15_1.append((i.address,j.address,v,("%08X"%c[0]) if c else "NONE"))
                    break
print("  total WhatAmI vcalls [..+0x2c]: %d"%vc)
print("  cmp value distribution:",dict(cnt))
print("  cmp against 15/1 hits (count=%d):"%len(hits15_1))
for a,b,v,fn in hits15_1:
    print("    vcall@%08X cmp@%08X val=%d fn=%s"%(a,b,v,fn))
