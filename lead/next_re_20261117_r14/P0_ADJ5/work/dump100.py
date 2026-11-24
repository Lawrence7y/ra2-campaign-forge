#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump first-100 rows with ENUM evidence + my features for careful adjudication."""
import csv, collections
from pathlib import Path
ROOT=Path(r'D:\Project\ra2-campaign-forge')
WD=ROOT/r'lead\next_re_20261117_r14\P0_ADJ5\work'
ENUM=ROOT/r'lead\next_re_20261117_r14\P0_RESIDUAL_2\ENUM.tsv'

# load not-in-cov sorted
addrs=[int(l.strip(),16) for l in open(WD/'undecidable_not_in_cov.tsv',encoding='utf-8') if l.strip()]
addrs=sorted(set(addrs))[:100]

# load ENUM evidence by addr
ev={}
with open(ENUM,encoding='utf-8-sig',newline='') as f:
    r=csv.reader(f,delimiter='\t'); next(r)
    for row in r:
        if len(row)<10: continue
        ev[row[0].strip().upper()]=(row[1],row[5],row[7],row[8],row[9])

# load my features
feats={}
with open(WD/'feats_all.tsv',encoding='utf-8') as f:
    next(f)
    for line in f:
        p=line.rstrip('\n').split('\t')
        feats[p[0]]=(p[1],p[2],p[3],p[4],p[5],p[6],p[7])

ch=collections.Counter()
print('idx addr      chan          pred  first_insn                    aC aJ bV c  c_ev                 d')
for i,a in enumerate(addrs):
    key=f'{a:08X}'
    chn,pred,finsn,ureas,e=ev.get(key,('?','?','?','?','?'))
    ch[chn]+=1
    aC,aJ,bV,c,ce,d,de=feats.get(key,('0','0','0','0','','','' ))
    print(f'{i:3d} {key} {chn:13s} {pred:5s} {finsn[:30]:30s} {aC}  {aJ}  {bV}  {c}  {ce[:20]:20s} {d}')
print('channel dist first100:',dict(ch))
