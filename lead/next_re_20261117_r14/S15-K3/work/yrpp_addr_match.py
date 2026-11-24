#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Match each candidate address against any address literal in YRpp headers, with surrounding context."""
import os, re
YRPP = r"D:\Project\ra2-campaign-forge\YRpp"
CAND = [
0x006D0F00,0x006D6070,0x006E1830,0x006E2A10,0x006E2AA0,0x006E4790,
0x006E47C0,0x006E6310,0x006EA3E0,0x006F1920,0x0070F120,0x0071FA30,
0x00721270,0x00726910,0x00727AA0,0x0072DDB0,0x0072DEF0,0x00751590,
0x00752460,0x00763610,0x00763690,
]
# collect all lines with hex addresses from YRpp
addr_lines=[]
pat=re.compile(r'0x0*([0-9A-Fa-f]{6,8})\b')
for root,dirs,files in os.walk(YRPP):
    for fn in files:
        if not fn.lower().endswith(('.h','.hpp','.cpp','.c')): continue
        fp=os.path.join(root,fn)
        try:
            with open(fp,encoding='utf-8',errors='replace') as f:
                for ln,line in enumerate(f,1):
                    for m in pat.finditer(line):
                        try: v=int(m.group(1),16)
                        except: continue
                        if 0x400000<=v<0xC00000:
                            addr_lines.append((v,fp,ln,line.rstrip()))
        except: pass

print(f"total YRpp address literals: {len(addr_lines)}")
print()
for c in CAND:
    matches=[x for x in addr_lines if x[0]==c]
    print("="*80)
    print(f"0x{c:08X}: {len(matches)} exact YRpp address matches")
    for v,fp,ln,line in matches:
        print(f"  {os.path.basename(fp)}:{ln}: {line.strip()}")
