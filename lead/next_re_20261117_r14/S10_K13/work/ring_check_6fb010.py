import sys,csv,hashlib,struct
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\work')
import re_lib as R
ROOT=Path(r'D:\Project\ra2-campaign-forge')
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
with COV.open(encoding='utf-8',newline='') as f: cov={r['entry'].strip().lower():r for r in csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t')}
L=['S10_K13 006FB010 RINGS','EXE_SHA='+hashlib.sha256(R.EXE.read_bytes()).hexdigest().upper()]
L.append('=== RING1 mission table 0x816CAC[0..31] ===')
for i in range(32):
 p=R.u32(0x816CAC+4*i); L.append(f'{i}:{R.cstring(p,80) if p else "?"}')
L.append('\n=== RING2 own function writes ===')
L.append(R.dis(0x6FB010,97))
L.append('\n=== RING3 direct caller 00736D3E in 00736CA0 (UnitClass::slot265) ===')
L.append(R.dis(0x736CA0,240))
L.append('\n=== RING4 external callees ===')
for va,nm in [(0x6FB080,'TechnoClass::StartReloading'),(0x6FCFA0,'not used here'),(0x523340,'WhatAmI')]:
 r=cov.get(f'{va:08X}'.lower())
 L.append(f'{nm} {va:08X} disk=' + (f'{r["subsystem"]}|{r["grade"]}|{r["name"]}' if r else 'NOT_IN_COV'))
L.append('\n--- 006FB080 bytes ---')
L.append(R.dis(0x6FB080,224))
L.append('\n--- 006FCDB0 virtual location evidence (already proved, external to batch) ---')
r=cov.get('006fcdb0'); L.append(f'006FCDB0 disk={r["subsystem"]}|{r["grade"]}|{r["name"]}' if r else 'NOT_IN_COV')
L.append(R.dis(0x6FCDB0,80))
out=ROOT/'lead/next_re_20261117_r14/S10_K13/EVIDENCE/PROOF_6FB010.txt'
out.write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('WROTE',out)
