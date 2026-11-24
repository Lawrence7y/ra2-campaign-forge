import sys,csv,hashlib,datetime
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\work')
import re_lib as R
ROOT=Path(r'D:\Project\ra2-campaign-forge')
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
def rd(path,enc='utf-8'):
 with path.open(encoding=enc,newline='') as f:return list(csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t'))
cov={r['entry'].strip().lower():r for r in rd(COV)}
atl={r['entry'].strip().lower():r for r in rd(ATL,'utf-8-sig')}
L=['S10_K13 PROOF 004D85D0','TIME='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'EXE_SHA='+hashlib.sha256(R.EXE.read_bytes()).hexdigest().upper()]
r=cov.get('004d85d0');a=atl.get('004d85d0');sz=int(a.get('size','0'),0) if a and a.get('size') else 0x10c8
L.append('OWNER_DISK='+(f'{r["subsystem"]}\t{r["grade"]}\t{r["name"]}\t{r["one_line_semantics"]}' if r else 'NOT_IN_COV'))
L.append('ATLAS_SIZE='+str(sz))
L.append('\n=== FULL BODY ===')
L.append(R.dis(0x4D85D0,sz))
L.append('\n=== RING3 DIRECT CALLERS ===')
for site,va,label in [(0x51A9FC,0x519630,'00519630 InfantryClass::slot99'),(0x73A4FB,0x739EC0,'00739EC0 UnitClass::slot99'),(0x73B0A0,0x739EC0,'00739EC0 second call')]:
 L.append('\n--- '+label+' @ '+f'{site:08X}'+' ---')
 lo=max(va,site-80); hi=site-va+24
 L.append(R.dis(lo,hi))
L.append('\n=== RING4 EXTERNAL PROVED CALLEES ===')
for va,nm,sz2 in [(0x5657A0,'MapClass::TryGetCellAt',120),(0x65C7E0,'Randomizer::RandomRanged',100)]:
 rr=cov.get(f'{va:08X}'.lower());L.append(f'{nm} {va:08X} '+(f'{rr["subsystem"]}\t{rr["grade"]}\t{rr["name"]}\t{rr["one_line_semantics"]}' if rr else 'NOT_IN_COV'));L.append(R.dis(va,sz2))
L.append('\n=== RING1 CONSTANTS ===')
L.append('arg0 == 2 is tested at function entry; subcell offsets use 8-entry table 0x89F688; final RandomRanged arguments are 0 and 2.')
out=ROOT/'lead/next_re_20261117_r14/S10_K13/EVIDENCE/PROOF_4D85D0.txt'
out.write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('WROTE',out,'lines',len(L),'size',sz)
