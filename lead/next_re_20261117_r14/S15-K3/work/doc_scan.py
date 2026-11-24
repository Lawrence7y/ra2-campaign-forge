#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Single-pass scan: find candidate addresses in project docs and show lines with name context."""
import os, re
ROOT=r"D:\Project\ra2-campaign-forge"
CAND = ['006D6070','006E1830','006E4790','006E47C0','006E6310','006EA3E0','006F1920',
        '0070F120','0071FA30','00721270','00726910','00727AA0','0072DDB0','0072DEF0',
        '00751590','00752460','00763610','00763690','006E2A10','006E2AA0']
# only doc-like files, skip huge raw data
EXT={'.md','.txt','.tsv','.json','.py','.cpp','.h','.hpp'}
skipdirs={'_ghidra','_ghidra_proj','.git','.asar-dump','ra2youli','extracted','node_modules','__pycache__'}
results={c:[] for c in CAND}
for root,dirs,files in os.walk(ROOT):
    dirs[:]=[d for d in dirs if d not in skipdirs]
    for fn in files:
        if os.path.splitext(fn)[1].lower() not in EXT: continue
        fp=os.path.join(root,fn)
        try:
            if os.path.getsize(fp)>5_000_000: continue
            with open(fp,encoding='utf-8',errors='replace') as f:
                for ln,line in enumerate(f,1):
                    for c in CAND:
                        if c in line.upper() or ('0X'+c) in line.upper():
                            if len(results[c])<8:
                                results[c].append((fp,ln,line.rstrip()))
        except: pass
for c in CAND:
    rs=results[c]
    print("="*70)
    print(f"{c}: {len(rs)} doc hits")
    for fp,ln,line in rs:
        rel=fp.replace(ROOT+'\\','')
        print(f"  {rel}:{ln}: {line[:200]}")
