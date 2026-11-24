#!/usr/bin/env python3
"""Write per-card detail line blocks to EVIDENCE (UTF-8 direct)."""
import os
from collections import defaultdict
ROOT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
N=os.path.join(ROOT,'N_FIX')
rows=defaultdict(list)
for line in open(os.path.join(N,'NOINIT_CENSUS.tsv'),encoding='utf-8'):
    p=line.rstrip('\n').split('\t')
    if p[0]=='addr': continue
    rows[p[1].split('/')[0]].append(p)
out=[]
for c in sorted(rows):
    out.append(f"\n#### {c} — {len(rows[c])} census 行")
    for p in rows[c]:
        addr,_,name,grade,should,sgrade,ev=p
        out.append(f"- `{addr}` 现=`{name}` [{grade}] → 应为=`{should}` [{sgrade}]（{ev}）")
with open(os.path.join(N,'EVIDENCE','card_detail_block.txt'),'w',encoding='utf-8') as f:
    f.write("\n".join(out)+"\n")
print("wrote", len(rows), "cards")
