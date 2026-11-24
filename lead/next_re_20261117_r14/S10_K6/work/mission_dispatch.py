#!/usr/bin/env python3
import csv,sys,collections
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K6\work')
import re_lib as R
root=Path(r'D:\Project\ra2-campaign-forge')
cov=[]
with (root/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv').open('r',encoding='utf-8',newline='') as f:
 for r in csv.DictReader(f,delimiter='\t'):
  if r['subsystem'].strip().upper()=='S10': cov.append(r)
by={r['entry'].strip().lower():r for r in cov}
names=['Sleep','Attack','Move','QMove','Retreat','Guard','Sticky','Enter','Capture','Eaten','Harvest','Area Guard','Return','Stop','Ambush','Hunt','Unload','Sabotage','Construction','Selling','Repair','Rescue','Missile','Harmless','Open','Patrol','Paradrop Approach','Paradrop Overfly','Wait','Attack Move','Spyplane Approach','Spyplane Overfly']
tab=[R.u32(0x5B34E8+4*i) for i in range(32)]
out=[]
for i,t in enumerate(tab):
 row=by.get(f'{t:08x}'.lower())
 tag=''
 if row: tag=f"cov={row['grade'].strip()} name={row['name']}"
 out.append(f'id {i:2d} {names[i]:20s} -> {t:08X} {tag}')
out.append('\n=== unique case bodies ===')
seen=[]
for i,t in enumerate(tab):
 if t in seen: continue
 seen.append(t)
 out.append(f'\n--- id {i} {names[i]} @ {t:08X} ---')
 out.append(R.block(t,count=80,max_bytes=2048))
out.append('\n=== S10 rows 005B2D00-005B3BFF ===')
for e,r in sorted(by.items()):
 v=int(e,16)
 if 0x5b2d00<=v<=0x5b3bff:
  out.append(f"{e.upper()}\t{r['name']}\t{r['grade']}\t{r['one_line_semantics']}")
txt='\n'.join(out)
p2=root/'lead/next_re_20261117_r14/S10_K6/EVIDENCE/mission_dispatch_cases.txt';p2.write_text(txt,encoding='utf-8')
print(f'WROTE {p2} {len(txt)} bytes')
print('\n'.join(out[:140]))
