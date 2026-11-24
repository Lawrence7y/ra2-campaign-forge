#!/usr/bin/env python3
"""Generate S10-K6 untruncated four-ring evidence for QueueMission callers."""
from pathlib import Path
import csv,datetime,hashlib,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import re_lib as R
root=Path(r'D:\Project\ra2-campaign-forge')
card=root/'lead/next_re_20261117_r14/S10_K6'
COV=root/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=root/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
def load(p):
 with p.open('r',encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
cov={r['entry'].strip().lower():r for r in load(COV)}
atl={r['entry'].strip().lower():r for r in load(ATL)}
rows=[
 ('004DF320','AircraftClass::QueueMissionId2Or1_If5C8Or5CC','Ring1 id 2/1. Clears [this+0x5D1]; if [this+0x5C8]!=0 queues id 2 target 1; else if [this+0x5CC]!=0 queues id 1 target 1. Ring3 push target/id with ecx=this. Ring2/4 QueueMission writes [this+0xB4]=id and [this+0xB8]=0.'),
 ('004DF3A0','AircraftClass::QueueMissionId1_AfterCellTargetCheck','Ring1 id 1. Clears/restores [this+0x2B4], builds target from [this+0x9C], checks [v+0x39C], queues id 1 target 1, writes [this+0x5D1]=1. Ring3 push 1/push 1 with ecx=this. Ring2/4 QueueMission writes [this+0xB4]/[this+0xB8].'),
 ('004DFA70','AircraftClass::QueueMissionId9_AfterNearestUnitSearch','Ring1 id 9. Scans House +0xA8/+0x9C by squared distance, calls [v+0x480] on selected object, queues id 9 target 0. Ring3 push 0/push 9 with ecx=this. Ring2/4 QueueMission writes [this+0xB4]/[this+0xB8].'),
 ('00521760','InfantryClass::QueueMissionId5Or15_OnOwnerCheck','Ring1 ids 5/15. Stack arg gates 0x5F5940; owner House pointer [this+0x21C] selects id 5 else id 15, target 0; then [v+0x558](0x21,1,0). Ring3 push 0/push 5 or push 0/push 0xF with ecx=this. Ring2/4 QueueMission writes [this+0xB4]/[this+0xB8].'),
 ('006F4960','AircraftClass::QueueMissionId15_OnMissionId14','Ring1 id 15. Writes [this+0x41C]=1; caller House != global and current mission [v+0x184]==0xE => queues id 15 target 0; writes [this+0x41B], House +0x5778/+0x5779/+0x1F4. Ring3 push 0/push 0xF with ecx=this. Ring2/4 QueueMission writes [this+0xB4]/[this+0xB8].'),
]
sha=hashlib.sha256((root/'ra2youli/gamemd.exe').read_bytes()).hexdigest().upper()
st=COV.stat(); out=[]
out.append('S10-K6 QUEUE-MISSION FOUR-RING EVIDENCE (untruncated)')
out.append('READ_TIME_ISO='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat())
out.append('EXE_SHA256='+sha)
out.append('COVERAGE_MTIME_ISO='+datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone(datetime.timedelta(hours=8))).isoformat()+' SIZE='+str(st.st_size))
out.append('TOOLS=Python3.12.10 capstone5.0.7(skipdata=True) pefile2024.8.26; no Ghidra; target read-only')
out.append('')
out.append('=== RING 1: key enum constants (mission id domain) ===')
out.append('Mission id domain is the proved 32-entry table at 0x816CAC (exclusive end 0x816D2C) and dispatch cmp eax,0x1F @0x005B30B8.')
out.append('Name strings below are printed only to show the enum domain; NO name is used to derive any new method name.')
for i in range(32):
 p=0x816CAC+4*i; q=R.u32(p)
 out.append('id %2d slot=%08X ptr=%08X str=%r'%(i,p,q,R.cstr(q,80)))
out.append('')
out.append(R.block(0x5B30B2,count=20,max_bytes=64))
out.append('')
out.append('=== RING 4 + RING 2: QueueMission and SetMission callee bytes ===')
out.append('QueueMission 005B35E0: [esp+4]=mission id; writes dword [this+0xB4]=id and byte [this+0xB8]=0; if [esp+0xC]!=0 and [v+0x200] true calls SetMission v[123].')
out.append(R.block(0x5B35E0,count=80,max_bytes=256))
out.append('')
out.append('SetMissionFromQueue 005B3570: copies [this+0xB4]->[this+0xAC], clears +0xB4 to -1, writes timer +0xC8/+0xCC/+0xD0 and flags +0xBC/+0xC0/+0xC4.')
out.append(R.block(0x5B3570,count=100,max_bytes=256))
for e,name,ring in rows:
 row=cov[e.lower()]; ar=atl[e.lower()]; va=int(e,16); size=int(ar.get('size','0') or 0)
 out.append(''); out.append('===== '+e+' =====')
 out.append('baseline_row='+repr(row))
 out.append('new_name='+name)
 out.append('atlas_size='+str(size))
 out.append('RTTI/VFTABLE (class channel only; never used alone as semantics):')
 for ref,best in R.find_vtable_containing(va,max_back=512): out.append('ref=%08X best=%s'%(ref,best))
 out.append('RING SUMMARY: '+ring)
 out.append('FULL BOUNDED DISASSEMBLY:')
 for i in R.MD.disasm(R.read(va,min(size,6000)),va):
  if i.id==0: out.append('%08X %s .byte'%(i.address,i.bytes.hex(' ')))
  else: out.append(R.fmt(i))
 out.append('')
 out.append('NAME DERIVATION: behavior-only; class from RTTI vtable, role from numeric mission id + caller arguments + field writes + QueueMission/SetMission bytes; no mission-name string, Class::slotN, vslotN, or sub_ name used.')
(card/'EVIDENCE/QUEUE_MISSION_S10_PROOFS.txt').write_text('\n'.join(out)+'\n',encoding='utf-8')
print('WROTE',len('\n'.join(out)))
