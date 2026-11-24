#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find GetMapCoords-like funcs: read [reg+0x9C]/[reg+0xA0] then sar 8 -> short store."""
import re, sys, bisect
from core_disasm import get_insns
D=get_insns(); INS=D["insns"]
addrs=[x[0] for x in INS]

def dump(a,b):
    i=bisect.bisect_left(addrs,a); j=bisect.bisect_left(addrs,b)
    for (x,s,m,o) in INS[i:j]:
        print("%08X  %-8s %s"%(x,m,o))

# find all reads of [reg+0x9C] in Building region 0x43xxxx and other known obj funcs
hits=[]
for idx,(a,s,m,o) in enumerate(INS):
    if re.search(r'\[\w+ \+ 0x9c\]',o) and (0x400000<=a<0x7e0000):
        hits.append((a,m,o))
print("reads of [reg+0x9C]:",len(hits))
# Show those with a nearby sar 8 (within 12 insns)
shown=0
for a,m,o in hits:
    i=bisect.bisect_left(addrs,a)
    win=INS[i:i+14]
    if any(x[2]=='sar' and x[3].strip().endswith(', 8') for x in win):
        print("\n--- @%08X ---"%a)
        dump(a, INS[i+12][0]+8 if i+12<len(INS) else a+80)
        shown+=1
        if shown>=12: break
