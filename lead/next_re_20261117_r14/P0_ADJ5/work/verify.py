#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify the sweep/vtable index against known positives, and inspect pool construction."""
import pickle, csv, collections
from pathlib import Path
ROOT=Path(r'D:\Project\ra2-campaign-forge')
WD=ROOT/r'lead\next_re_20261117_r14\P0_ADJ5\work'
idx=pickle.load(open(WD/'idx.pkl','rb'))
calls=idx['calls']; jmps=idx['jmps']; vtgt=idx['vtgt']

# Known positive: ENUM line 11 says 0x402F80 = "call 0x4093b0" -> 0x4093B0 is a call target
print('0x4093B0 in calls?', 0x4093B0 in calls, 'sites', [hex(x) for x in calls.get(0x4093B0,[])][:5])
# Known project facts: distinct call targets should be 6728
print('distinct call targets', len(calls))
# a few known coverage function entries that are call targets
for a in (0x4C9150,0x5657A0,0x7C978A,0x7C8B3D):
    print(f'{a:08X} call?', a in calls, 'vt?', a in vtgt, 'jmp?', a in jmps)

# channel distribution among UNDECIDABLE
enum=ROOT/r'lead\next_re_20261117_r14\P0_RESIDUAL_2\ENUM.tsv'
ch=collections.Counter(); npool=0
with open(enum,encoding='utf-8-sig',newline='') as f:
    r=csv.reader(f,delimiter='\t'); hdr=next(r)
    for row in r:
        if len(row)<3: continue
        if row[2].strip()=='UNDECIDABLE':
            npool+=1
            ch[row[1].strip()]+=1
print('UNDECIDABLE channel dist:', dict(ch), 'total', npool)

# evidence field flags among UNDECIDABLE (call/jmp/ptr/fpu)
flags=collections.Counter()
with open(enum,encoding='utf-8-sig',newline='') as f:
    r=csv.reader(f,delimiter='\t'); hdr=next(r)
    for row in r:
        if len(row)<10 or row[2].strip()!='UNDECIDABLE': continue
        ev=row[9]
        for k in ('call','jmp','ptr','fpu','inbody'):
            import re
            m=re.search(k+r'=(\d+)',ev)
            if m: flags[(k,m.group(1))]+=1
print('evidence flags:', dict(flags))
