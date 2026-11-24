#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Targeted scan of reference corpora for candidate addresses (single pass)."""
import os
ROOT=r"D:\Project\ra2-campaign-forge"
CAND = ['006D6070','006E1830','006E4790','006E47C0','006E6310','006EA3E0','006F1920',
        '0070F120','0071FA30','00721270','00726910','00727AA0','0072DDB0','0072DEF0',
        '00751590','00752460','00763610','00763690','006E2A10','006E2AA0','006D0F00']
TARGETS=['ref','docs','re_atlas','out','tools','extracted','ra2re']
EXT={'.md','.txt','.tsv','.json','.py','.cpp','.h','.hpp','.xml','.csv'}
results={c:[] for c in CAND}
nfiles=0
for td in TARGETS:
    base=os.path.join(ROOT,td)
    if not os.path.isdir(base): continue
    for root,dirs,files in os.walk(base):
        dirs[:]=[d for d in dirs if d not in ('_ghidra','node_modules','__pycache__')]
        for fn in files:
            if os.path.splitext(fn)[1].lower() not in EXT: continue
            fp=os.path.join(root,fn)
            try:
                if os.path.getsize(fp)>3_000_000: continue
                nfiles+=1
                with open(fp,encoding='utf-8',errors='replace') as f:
                    for ln,line in enumerate(f,1):
                        U=line.upper()
                        for c in CAND:
                            if c in U or ('0X'+c) in U:
                                if len(results[c])<6:
                                    results[c].append((fp,ln,line.rstrip()))
            except: pass
print("files scanned:",nfiles)
for c in CAND:
    rs=results[c]
    if not rs: continue
    print("="*70)
    print(f"{c}: {len(rs)} hits")
    for fp,ln,line in rs:
        print(f"  {fp.replace(ROOT+chr(92),'')}:{ln}: {line[:220]}")
