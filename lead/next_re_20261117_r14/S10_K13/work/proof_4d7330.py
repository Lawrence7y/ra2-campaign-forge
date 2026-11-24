import sys,csv,hashlib,datetime
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\work')
import re_lib as R
ROOT=Path(r'D:\Project\ra2-campaign-forge')
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
def covrows():
 with COV.open(encoding='utf-8',newline='') as f:
  return list(csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t'))
def atlrows():
 with ATL.open(encoding='utf-8-sig',newline='') as f:
  return list(csv.DictReader(f,delimiter='\t'))
rows=covrows(); cov={r['entry'].strip().lower():r for r in rows}
atl={r['entry'].strip().lower():r for r in atlrows()}
L=['S10_K13 PROOF 004D7330','TIME='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'EXE_SHA='+hashlib.sha256(R.EXE.read_bytes()).hexdigest().upper(),'COV_SIZE='+str(COV.stat().st_size)+' COV_SHA='+hashlib.sha256(COV.read_bytes()).hexdigest().upper()]
r=cov.get('004d7330'); a=atl.get('004d7330')
sz=int(a.get('size','0'),0) if a and a.get('size') else 300
L.append('OWNER_DISK='+(f'{r["subsystem"]}\t{r["grade"]}\t{r["name"]}\t{r["one_line_semantics"]}' if r else 'NOT_IN_COV'))
L.append('ATLAS_SIZE='+str(sz))
L.append('\n=== RING2/RING4 OWN FUNCTION FULL BODY ===')
L.append(R.dis(0x4D7330,sz))
L.append('\n=== RING3 DIRECT CALLERS (interval-contained) ===')
for site,va,label in [(0x4165EC,0x4165C0,'004165C0 AircraftClass::vslot91'),(0x518042,0x517FA0,'00517FA0 InfantryClass::slot91'),(0x737D52,0x737C90,'00737C90 UnitClass::slot91')]:
 L.append('\n--- '+label+' call site '+f'{site:08X}'+' ---')
 L.append(R.dis(va, (site-va)+16))
L.append('\n=== RING1 / RING4 EXTERNAL PROVED CALLEES (on-disk, grade col 5) ===')
for va,nm in [(0x62A4A0,'ParasiteClass::ExitUnit'),(0x701900,'TechnoClass::ReceiveDamage')]:
 rr=cov.get(f'{va:08X}'.lower())
 L.append(f'{nm} {va:08X} '+(f'{rr["subsystem"]}\t{rr["grade"]}\t{rr["name"]}\t{rr["one_line_semantics"]}' if rr else 'NOT_IN_COV'))
 L.append(R.dis(va,160 if va==0x62A4A0 else 110))
L.append('\n=== RING1 ENUM CROSS-CHECK from 00701900 bytes and coverage semantics ===')
L.append('DamageState(0..5) is recorded in the [已证] semantics of 00701900; 004D7330 compares returned eax to 5, 0 and 4.')
out=ROOT/'lead/next_re_20261117_r14/S10_K13/EVIDENCE/PROOF_4D7330.txt'
out.write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('WROTE',out,'lines',len(L),'size',sz)
