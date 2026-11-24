#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, bisect
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_GATE_B\work')
ATLAS=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
rows=[]
with open(ATLAS,encoding='utf-8',errors='replace') as f:
    for line in f:
        p=line.rstrip('\n').split('\t')
        if len(p)>=2:
            try: rows.append((int(p[0],16),int(p[1]),p))
            except: pass
rows.sort(); starts=[r[0] for r in rows]
def cont(va):
    idx=bisect.bisect_right(starts,va)-1
    for j in range(idx,max(-1,idx-6),-1):
        e,s,p=rows[j]
        if e<=va<e+s: return e,s,p
    return None
for site in (0x4B2BCD,0x4B30B2,0x516A41,0x6A221D,0x6A2702):
    c=cont(site)
    print("setg selector site 0x%08X -> fn %s"%(site, ("0x%08X size=%d"%(c[0],c[1])) if c else "NONE"))
