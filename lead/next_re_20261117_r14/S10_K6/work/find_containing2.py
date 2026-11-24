#!/usr/bin/env python3
import csv
from pathlib import Path
root=Path(r'D:\Project\ra2-campaign-forge')
def load(p):
 with p.open('r',encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
atl=load(root/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv');cov={r['entry'].strip().lower():r for r in load(root/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv')}
for a in [0x417040,0x419E41,0x419EC7,0x419F26,0x4406A0,0x716187,0x7161B7,0x785E5B,0x785E81,0x78952F,0x799252,0x4D23AE,0x4D279F,0x5F5BFA]:
 hits=[r for r in atl if int(r['entry'],16)<=a<int(r['entry'],16)+int(r.get('size','0') or 0)]
 print(hex(a),[(h['entry'],h.get('size'),cov.get(h['entry'].lower(),{}).get('name')) for h in hits])
