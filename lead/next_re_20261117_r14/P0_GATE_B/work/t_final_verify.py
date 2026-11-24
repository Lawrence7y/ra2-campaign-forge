#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final verify: 0x47C3D0 is type-agnostic (no WhatAmI vcall); selector branches;
   RTTI fail-closed; callers of the 10 callsite functions."""
import sys, struct, bisect
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_GATE_B\work')
import peutil
from peutil import *
def is_data(i): return i.id==0 or i.mnemonic.startswith('.')

# RTTI correct chain (.rdata range)
VT=0x7E3EBC
col=u32(VT-4)
print("RTTI: VT=0x%08X COL=0x%08X"%(VT,col))
if 0x7E1000<=col<0x812000:
    td=u32(col+0xc); print("  COL+0xC TD=0x%08X"%td)
    if 0x7E1000<=td<0x812000 or 0x812000<=td<0xB79BE4:
        nm=read(td+8,48)
        print("  TD+8 inline name: %r"%nm)
    else:
        print("  TD invalid -> name='?' (fail-closed)")
else:
    print("  COL invalid -> name='?' (fail-closed)")

# 0x47C3D0: confirm no WhatAmI vcall [..+0x2c], list selector branch
print("\n0x47C3D0 (0x47C3D0..0x47C4C7) WhatAmI-vcall count and selector branch:")
vc=0; sel=[]
for i in disasm(0x47C3D0,0x100,skipdata=True):
    if is_data(i) or i.address>=0x47C4C8: continue
    if i.mnemonic=='call' and i.operands and i.operands[0].type==X86_OP_MEM and i.operands[0].mem.disp==0x2c:
        vc+=1
    if '0xe8' in i.op_str or '0xe4' in i.op_str or i.mnemonic=='setg':
        sel.append(fmt_insn(i))
print("  WhatAmI vcall [reg+0x2c] count = %d"%vc)
for s in sel: print("  "+s)

# callers of the 10 containing functions
ATLAS=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
rows=[]
with open(ATLAS,encoding='utf-8',errors='replace') as f:
    for line in f:
        p=line.rstrip('\n').split('\t')
        if len(p)>=2:
            try: rows.append((int(p[0],16),int(p[1])))
            except: pass
CONTAIN=[0x43F180,0x449440,0x47EC90,0x588570,0x588750,0x5FC570,0x6D59D0,0x6D5C50,0x716150,0x71C4D0]
print("\nDirect E8 callers (whole .text) of the 10 containing functions:")
tb=read(0x401000,0x7E1000-0x401000)
for f in CONTAIN:
    sites=[]
    for i in range(len(tb)-5):
        if tb[i]==0xE8:
            rel=struct.unpack_from('<i',tb,i+1)[0]; a=0x401000+i
            if a+5+rel==f: sites.append(a)
    print("  fn 0x%08X : %d direct callers %s"%(f,len(sites),[hex(x) for x in sites[:12]]))
