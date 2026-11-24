import sys,csv,hashlib
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\work')
import re_lib as R
ROOT=Path(r'D:\Project\ra2-campaign-forge')
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
with ATL.open(encoding='utf-8-sig',newline='') as f: atl={r['entry'].strip().lower():r for r in csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t')}
with COV.open(encoding='utf-8',newline='') as f: cov={r['entry'].strip().lower():r for r in csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t')}
targets=[0x6FB010,0x7059F0,0x739EC0,0x519630,0x51CDB0,0x51D0D0,0x707D20,0x709820,0x7360C0,0x737BA0,0x737C90,0x743A50,0x4D5690,0x706FA0,0x6FB080,0x70DDD0,0x701900,0x710550,0x6B7BB0,0x70D690]
L=['S10_K13 TARGETED DISASM','EXE_SHA='+hashlib.sha256(R.EXE.read_bytes()).hexdigest().upper()]
for va in targets:
    k=f'{va:08X}'.lower(); r=cov.get(k); a=atl.get(k)
    try:sz=int(a.get('size','0'),0) if a and a.get('size') else 0
    except:sz=0
    if not sz:sz=512
    L.append('\n=== '+f'{va:08X}'+' size='+str(sz)+' name='+(r['name'] if r else '?')+' grade='+(r['grade'] if r else '?')+' sem='+(r['one_line_semantics'] if r else '')+' ===')
    L.append(R.dis(va,min(sz,6000)))
out=ROOT/'lead/next_re_20261117_r14/S10_K13/EVIDENCE/TARGETED_DISASM.txt'
Path(out).write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('WROTE',out,'lines',len(L))
