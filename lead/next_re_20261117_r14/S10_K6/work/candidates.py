#!/usr/bin/env python3
import csv
from pathlib import Path
R=Path(r'D:\Project\ra2-campaign-forge')
cov=R/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
atl=R/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
def load(p):
 with p.open('r',encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
a={r['entry'].strip().lower():r for r in load(atl)}
rows=[r for r in load(cov) if r['subsystem'].strip().upper()=='S10' and r['grade'].strip()!='[已证]' and r['entry'].strip().lower() in a]
with open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K6\EVIDENCE\candidates_nonproved.tsv','w',encoding='utf-8',newline='') as f:
 w=csv.writer(f,delimiter='\t',lineterminator='\n')
 w.writerow(['entry','name','grade','sem','evidence','atlas_name','atlas_sem','atlas_size'])
 for r in rows:
  ar=a[r['entry'].strip().lower()]
  w.writerow([r['entry'],r['name'],r['grade'],r['one_line_semantics'],r['evidence_path'],ar.get('class',''),ar.get('method',''),ar.get('size','')])
print('rows',len(rows))
