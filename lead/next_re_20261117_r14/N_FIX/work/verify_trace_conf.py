#!/usr/bin/env python3
"""Verify conf/source in classification_trace.tsv for census addresses per card."""
import json, os
from collections import defaultdict
ROOT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
D=os.path.join(ROOT,'N_FIX','EVIDENCE')
data=json.load(open(os.path.join(D,'census_detailed.json'),encoding='utf-8'))
census_addr=defaultdict(list)
for c in data['census']: census_addr[c['addr']].append(c)
uaddr=set(census_addr)

for n in range(1,11):
    card=f"C{n:02d}"
    t=os.path.join(ROOT,f"{card}_census","EVIDENCE","classification_trace.tsv")
    found={}
    if os.path.exists(t):
        for line in open(t,encoding='utf-8',errors='replace'):
            p=line.rstrip('\n').split('\t')
            if len(p)<4 or p[0]=='entry': continue
            try: a=int(p[0])
            except: continue
            if a in uaddr:
                # entry,sub,conf,grade,source,name,...
                found[a]=(p[2],p[3],p[4] if len(p)>4 else '',p[5] if len(p)>5 else '')
    print(f"\n=== {card}: {len(found)} census addrs in trace ===")
    for a in sorted(found):
        conf,grade,source,name=found[a]
        print(f"  0x{a:08X} conf={conf:<6} grade={grade:<10} source={source:<12} name={name}")
