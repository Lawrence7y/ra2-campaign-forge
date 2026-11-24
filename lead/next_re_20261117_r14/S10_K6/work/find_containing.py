#!/usr/bin/env python3
import csv
from pathlib import Path
root=Path(r'D:\Project\ra2-campaign-forge')
def load(p):
 with p.open('r',encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
atl=load(root/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'); cov={r['entry'].strip().lower():r for r in load(root/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv')}
for a in [0x449368,0x44c4db,0x45080d,0x457617,0x4c6fa2,0x4fdf32,0x5013d9,0x6ddf44,0x6e08ff,0x70a6f7,0x416613,0x5180f4,0x737dc9]:
 hits=[r for r in atl if int(r['entry'],16)<=a<int(r['entry'],16)+int(r.get('size','0') or 0)]
 print(hex(a),[(h['entry'],h.get('size'),cov.get(h['entry'].lower(),{}).get('name')) for h in hits])
