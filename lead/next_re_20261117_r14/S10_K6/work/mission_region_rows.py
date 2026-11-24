#!/usr/bin/env python3
import csv
from pathlib import Path
root=Path(r'D:\Project\ra2-campaign-forge')
with (root/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv').open('r',encoding='utf-8',newline='') as f:
 rows=[r for r in csv.DictReader(f,delimiter='\t') if r['subsystem'].strip().upper()=='S10']
out=[]
for r in sorted(rows,key=lambda x:int(x['entry'],16)):
 v=int(r['entry'],16)
 if 0x5b2d00<=v<=0x5b3c00 or (0x5f5d00<=v<=0x5f6000) or (0x65a900<=v<=0x65ac00):
  out.append(f"{r['entry']}\t{r['grade'].strip()}\t{r['name']}\t{r['one_line_semantics'][:180]}")
print('\n'.join(out))
