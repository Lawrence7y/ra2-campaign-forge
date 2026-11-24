#!/usr/bin/env python3
"""Build per-card impact numbers from the generated census TSV + trace conf (formatting only)."""
import os
from collections import Counter
ROOT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
N=os.path.join(ROOT,'N_FIX')

rows=[]
for line in open(os.path.join(N,'NOINIT_CENSUS.tsv'),encoding='utf-8'):
    p=line.rstrip('\n').split('\t')
    if p[0]=='addr': continue
    rows.append(p)

# trace conf/source per (card,addr)
trace={}
for n in range(1,11):
    card=f"C{n:02d}"
    t=os.path.join(ROOT,f"{card}_census","EVIDENCE","classification_trace.tsv")
    if not os.path.exists(t): continue
    for line in open(t,encoding='utf-8',errors='replace'):
        p=line.rstrip('\n').split('\t')
        if len(p)<5 or p[0]=='entry': continue
        trace[(card,p[0])]=(p[2],p[3],p[4])  # conf, grade(utf8), source

per=Counter()
for addr,card,name,grade,should,sgrade,ev in rows:
    cards=card.split('/')
    c=cards[0]
    per[(c,'rows')]+=1
    if 'noinit_t' in name: per[(c,'noinit_named')]+=1
    t=trace.get((c,addr))
    if t:
        conf=t[0]
        per[(c,'conf_'+conf)]+=1
    if name.startswith('sub_'): per[(c,'sub_named')]+=1

print(f"{'card':6} {'rows':>4} {'noinit':>6} {'sub_':>4} {'high':>4} {'low':>3} {'med':>3} {'NOTinTrace':>10}")
for n in range(1,11):
    c=f"C{n:02d}"
    print(f"{c:6} {per[(c,'rows')]:>4} {per[(c,'noinit_named')]:>6} {per[(c,'sub_named')]:>4} "
          f"{per[(c,'conf_high')]:>4} {per[(c,'conf_low')]:>3} {per[(c,'conf_med')]:>3} "
          f"{per[(c,'rows')]-per[(c,'conf_high')]-per[(c,'conf_low')]-per[(c,'conf_med')]:>10}")

print("\nTotal census TSV rows:",len(rows))
print("unique addrs:",len(set(r[0] for r in rows)))
