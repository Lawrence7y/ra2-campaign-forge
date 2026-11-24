#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-scan YRpp with a permissive address regex (allow u/U suffix, any case)."""
import os, re
YRPP = r"D:\Project\ra2-campaign-forge\YRpp"
CAND = {
0x006D0F00,0x006D6070,0x006E1830,0x006E2A10,0x006E2AA0,0x006E4790,
0x006E47C0,0x006E6310,0x006EA3E0,0x006F1920,0x0070F120,0x0071FA30,
0x00721270,0x00726910,0x00727AA0,0x0072DDB0,0x0072DEF0,0x00751590,
0x00752460,0x00763610,0x00763690,
}
# permissive: 0x + up to 8 hex, optional u, allow next char non-hex
pat=re.compile(r'0[xX]([0-9A-Fa-f]{5,8})[uUlL]?(?![0-9A-Fa-f])')
hits={c:[] for c in CAND}
n=0
for root,dirs,files in os.walk(YRPP):
    for fn in files:
        if not fn.lower().endswith(('.h','.hpp','.cpp','.c','.txt')): continue
        fp=os.path.join(root,fn)
        with open(fp,encoding='utf-8',errors='replace') as f:
            for ln,line in enumerate(f,1):
                for m in pat.finditer(line):
                    try: v=int(m.group(1),16)
                    except: continue
                    n+=1
                    if v in CAND:
                        hits[v].append((os.path.basename(fp),ln,line.rstrip()))
print("address literals parsed:",n)
for c in sorted(CAND):
    if hits[c]:
        print("="*70)
        print(f"0x{c:08X}:")
        for fp,ln,line in hits[c]:
            print(f"  {fp}:{ln}: {line.strip()}")
