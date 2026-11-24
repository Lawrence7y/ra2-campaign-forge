#!/usr/bin/env python3
"""Show ALL coverage_delta rows at census addresses for each card, with name/grade."""
import json, os
from collections import defaultdict
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
D = os.path.join(ROOT,'N_FIX','EVIDENCE')
data = json.load(open(os.path.join(D,'census_detailed.json'),encoding='utf-8'))
census_addr = defaultdict(list)
for c in data['census']:
    census_addr[c['addr']].append(c)
uaddr = set(census_addr)

for n in range(1,11):
    card=f"C{n:02d}"
    p=os.path.join(ROOT,f"{card}_census","coverage_delta.tsv")
    out=[]
    with open(p,encoding='utf-8',errors='replace') as fh:
        for line in fh:
            parts=line.rstrip('\n').split('\t')
            if len(parts)<5 or parts[0]=='entry': continue
            a=int(parts[0],16)
            if a in uaddr:
                real = census_addr[a][0]['real_cls']
                out.append((parts[0],parts[2],parts[4],real,len(census_addr[a])))
    print(f"\n=== {card}: {len(out)} rows at census addrs ===")
    for addr,name,grade,real,dup in sorted(out):
        flag = 'NOINIT' if 'noinit_t' in name else ('sub_' if name.startswith('sub_') else 'named')
        print(f"  {addr} | {flag:7} | {name:<40} | {grade} | real={real} dup={dup}")
