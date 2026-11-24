import sys,csv
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\work')
import re_lib as R
ROOT=Path(r'D:\Project\ra2-campaign-forge')
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
with COV.open(encoding='utf-8',newline='') as f: cov={r['entry'].strip().lower():r for r in csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t')}
addrs=[0x5F3DB0,0x4D03D0,0x62A4A0,0x701900,0x70F6A0,0x70F670,0x56BC50,0x5657A0,0x6B7BB0,0x70F6E0,0x706FA0,0x70DDD0,0x710550,0x70D690]
L=['EXTERNAL CALLEE STATUS (on-disk coverage, grade col 5 only)']
for va in addrs:
 r=cov.get(f'{va:08X}'.lower())
 if r:L.append(f'{va:08X}\t{r["subsystem"]}\t{r["grade"]}\t{r["name"]}\t{r["one_line_semantics"]}')
 else:L.append(f'{va:08X}\tNOT_IN_COV')
out=ROOT/'lead/next_re_20261117_r14/S10_K13/EVIDENCE/CALLEE_STATUS.txt'
Path(out).write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('\n'.join(L))
