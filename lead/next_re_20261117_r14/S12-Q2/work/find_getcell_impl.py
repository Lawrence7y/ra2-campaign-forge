#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find functions containing call 0x5657A0 (GetCellAt) with object-location-derived arg."""
import bisect, re
from core_disasm import get_insns
D=get_insns(); INS=D["insns"]; addrs=[x[0] for x in INS]

# indexes of all call 0x5657a0
callidx=[i for i,(a,s,m,o) in enumerate(INS) if m=='call' and '0x5657a0' in o]
print("call sites to GetCellAt:",len(callidx))
# For each, look back up to 30 insns for reads of [reg+0x9c]/[reg+0xa0] (object Location)
shown=0
for i in callidx:
    a=INS[i][0]
    win=INS[max(0,i-30):i]
    has_loc=any(re.search(r'\[\w+ \+ 0x(9c|a0|24|26)\]',x[3]) for x in win)
    if has_loc:
        print("\n=== call @%08X, preceding Location/mapcoord reads ==="%a)
        for (x,s,m,o) in INS[max(0,i-18):i+2]:
            print("%08X %-8s %s"%(x,m,o))
        shown+=1
        if shown>=10: break
