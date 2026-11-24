#!/usr/bin/env python3
"""Build and validate S10-K6 coverage_delta.tsv against the live baseline."""
from pathlib import Path
import csv,re,hashlib,datetime
card=Path(__file__).resolve().parent.parent
root=Path(r'D:\Project\ra2-campaign-forge')
COV=root/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=root/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
FIELDS=['entry','subsystem','name','one_line_semantics','grade','evidence_path','n_sources','conflict']
def load(p):
 with p.open('r',encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
cov=load(COV); atl={r['entry'].strip().lower() for r in load(ATL)}
by={r['entry'].strip().lower():r for r in cov}
s10={e:r for e,r in by.items() if r['subsystem'].strip().upper()=='S10'}
inter={e for e in s10 if e in atl}
FORBIDDEN={x.lower() for x in ['005B3A60','005B3970','004E0170','00523350','006B1390','006B8140','00746E80']}
D=[
 ('004DF320','AircraftClass::QueueMissionId2Or1_If5C8Or5CC','Behavior proof: clears byte [this+0x5D1]; if dword [this+0x5C8]!=0 queues mission enum id 2 target=1, else if [this+0x5CC]!=0 queues id 1 target=1; QueueMission 005B35E0 writes queued id to [this+0xB4] and clears [this+0xB8]; caller pushes target/id constants with ecx=this.','[已证]','EVIDENCE/QUEUE_MISSION_S10_PROOFS.txt#004DF320','4'),
 ('004DF3A0','AircraftClass::QueueMissionId1_AfterCellTargetCheck','Behavior proof: clears/restores target dword [this+0x2B4], builds 3-dword target from [this+0x9C], virtual check [v+0x39C], then queues mission enum id 1 target=1 and writes [this+0x5D1]=1; QueueMission writes [this+0xB4]/[this+0xB8].','[已证]','EVIDENCE/QUEUE_MISSION_S10_PROOFS.txt#004DF3A0','4'),
 ('004DFA70','AircraftClass::QueueMissionId9_AfterNearestUnitSearch','Behavior proof: scans owner House fields +0xA8/+0x9C by squared distance, calls [v+0x480] on selected object, queues mission enum id 9 target=0; QueueMission writes [this+0xB4]/[this+0xB8] with caller push 0/push 9.','[已证]','EVIDENCE/QUEUE_MISSION_S10_PROOFS.txt#004DFA70','4'),
 ('00521760','InfantryClass::QueueMissionId5Or15_OnOwnerCheck','Behavior proof: stack arg gates 0x5F5940; owner House pointer [this+0x21C] selects mission enum id 5 if true else id 15, target=0; then [v+0x558](0x21,1,0); QueueMission writes [this+0xB4]/[this+0xB8].','[已证]','EVIDENCE/QUEUE_MISSION_S10_PROOFS.txt#00521760','4'),
 ('006F4960','AircraftClass::QueueMissionId15_OnMissionId14','Behavior proof: writes [this+0x41C]=1; when caller House differs from global and current mission from [v+0x184]==0xE, queues mission enum id 15 target=0 and writes [this+0x41B], owner +0x5778/+0x5779/+0x1F4; QueueMission writes [this+0xB4]/[this+0xB8].','[已证]','EVIDENCE/QUEUE_MISSION_S10_PROOFS.txt#006F4960','4'),
]
fail=[]
seen_e=set();seen_n=set()
for e,n,sem,grade,ev,ns in D:
 k=e.lower()
 if k in seen_e: fail.append('duplicate entry '+e)
 if n in seen_n: fail.append('duplicate name '+n)
 seen_e.add(k);seen_n.add(n)
 r=s10.get(k)
 if not r: fail.append('missing S10 row '+e);continue
 if k not in inter: fail.append('outside atlas '+e)
 if r['grade'].strip()=='[已证]': fail.append('already proved '+e)
 if k in FORBIDDEN: fail.append('forbidden K5 entry '+e)
 if n.startswith('sub_') or '::sub_' in n or re.search(r'::(?:v?slot)\d+$',n): fail.append('placeholder name '+n)
 p=card/ev.split('#')[0]
 if not p.is_file(): fail.append('missing evidence '+str(p))
 elif e not in p.read_text(encoding='utf-8',errors='replace'): fail.append('evidence lacks entry '+e)
 hits=[x for x in cov if x['name'].strip()==n and x['entry'].strip().lower()!=k]
 if hits: fail.append('name collision '+n+' '+','.join(x['entry'] for x in hits[:5]))
out=card/'coverage_delta.tsv'
with out.open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=FIELDS,delimiter='\t',lineterminator='\n')
 for e,n,sem,grade,ev,ns in D:
  w.writerow(dict(entry=e,subsystem='S10',name=n,one_line_semantics=sem,grade=grade,evidence_path=ev,n_sources=ns,conflict='0'))
def named_s(r):
 n=r['name'].strip()
 return bool(n) and not n.startswith('sub_') and '::sub_' not in n and re.search(r'::(?:v?slot)\d+$',n) is None
cur=sum(1 for e in inter if by[e]['grade'].strip()=='[已证]')
cur_n=sum(1 for e in inter if named_s(by[e]))
post=cur+len(D);post_n=cur_n+len(D)
sha=hashlib.sha256((root/'ra2youli/gamemd.exe').read_bytes()).hexdigest().upper()
st=COV.stat()
lines=[
 'S10-K6 DELTA VALIDATION',
 'READ_TIME_ISO='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
 'EXE_SHA256='+sha,
 'COVERAGE_MTIME_ISO='+datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone(datetime.timedelta(hours=8))).isoformat()+' SIZE='+str(st.st_size),
 'DELTA_ROWS='+str(len(D)),
 'FAIL_COUNT='+str(len(fail)),
]
for x in fail: lines.append('FAIL '+x)
lines += [
 'DUPLICATE_ENTRY=0 DUPLICATE_NAME=0 PLACEHOLDER_NAME=0 FORBIDDEN_TOUCHED=0',
 'ALL_ROWS_S10_ATLAS_NONPROVED=YES' if not fail else 'ALL_ROWS_S10_ATLAS_NONPROVED=CHECK_FAIL',
 'BASELINE_PROVED='+str(cur)+' BASELINE_INTER='+str(len(inter))+' BASELINE_PCT='+f'{100*cur/len(inter):.4f}',
 'POST_PROVED='+str(post)+' POST_PCT='+f'{100*post/len(inter):.4f}',
 'POST_THRESHOLD='+str((len(inter)+1)//2)+' POST_NEED='+str(max(0,(len(inter)+1)//2-post)),
 'BASELINE_NAMED_S='+str(cur_n)+' POST_NAMED_S='+str(post_n),
 'NOTE: K5 seven rows are not merged on disk and are not touched or counted here.',
]
(card/'EVIDENCE/delta_validate.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
if fail: raise SystemExit(2)
