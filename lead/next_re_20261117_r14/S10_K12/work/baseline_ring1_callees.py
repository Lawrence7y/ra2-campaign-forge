
import sys,csv,hashlib,datetime,collections
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K12\work')
import re_lib as R
ROOT=Path(r'D:\Project\ra2-campaign-forge')
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
L=[]
def log(s=''):L.append(str(s))
log('S10_K12 BASELINE + RING1 + CALLEE GRADES')
log('TIME='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat())
log('COVERAGE='+str(COV)+' size='+str(COV.stat().st_size)+' sha256='+hashlib.sha256(COV.read_bytes()).hexdigest().upper()+' mtime='+datetime.datetime.fromtimestamp(COV.stat().st_mtime,datetime.timezone(datetime.timedelta(hours=8))).isoformat())
log('ATLAS='+str(ATL)+' size='+str(ATL.stat().st_size)+' sha256='+hashlib.sha256(ATL.read_bytes()).hexdigest().upper())

# baseline recompute: read only 5th column, case-normalize entries
with ATL.open(encoding='utf-8-sig',newline='') as f:
    atl={r['entry'].strip().lower() for r in csv.DictReader(f,delimiter='\t')}
with COV.open(encoding='utf-8',newline='') as f:
    rd=csv.DictReader(f,delimiter='\t')
    s10=[r for r in rd if r['subsystem'].strip().upper()=='S10']
inside=[r for r in s10 if r['entry'].strip().lower() in atl]
entries={r['entry'].strip().lower() for r in inside}
with COV.open(encoding='utf-8') as f:
    f.readline();ctr=collections.Counter()
    for line in f:
        z=line.rstrip('\n').split('\t')
        if z[0].strip().lower() in entries: ctr[z[4].strip().upper()]+=1
proved=ctr['[已证]']
log(f'S10_ROWS={len(s10)} S10_IN_ATLAS={len(inside)} S10_OUTSIDE={len(s10)-len(inside)}')
log('GRADE_5TH_COL='+repr(dict(ctr)))
log(f'PROVED={proved} PROVED_PCT={100*proved/len(inside):.4f} THRESHOLD={(len(inside)+1)//2}')
log('BASELINE_MATCH_K9='+str((len(inside),proved)==(526,107)))

# mission name table ring1
log('\n=== RING1 mission name table 0x816CAC[0..31] ===')
names=[]
for i in range(32):
    p=R.u32(0x816CAC+4*i)
    names.append(R.cstring(p,80) if p else '?')
log('TABLE='+'|'.join(f'{i}:{names[i]}' for i in range(32)))
log('YRPP_ENUM=27=ParadropOverfly 28=Wait 29=AttackMove 30=SpyplaneApproach 31=SpyplaneOverfly')

# external callee grades (full detail, write as ascii-safe by encoding markers)
log('\n=== EXTERNAL CALLEES (ledger, 5th col grade) ===')
with COV.open(encoding='utf-8',newline='') as f:
    cov={r['entry'].strip().lower():r for r in csv.DictReader(f,delimiter='\t')}
def det(va,nm):
    r=cov.get(f'{va:08X}'.lower())
    if not r: return f'{nm} {va:08X} NOT_IN_COV'
    return f'{nm} {va:08X} sub={r["subsystem"]} name={r["name"]} grade_marker={"P" if r["grade"].strip()=="[已证]" else ("I" if r["grade"].strip()=="[静态推断]" else "U")} conflict={r["conflict"]} src={r["n_sources"]}'
for va,nm in [(0x65C7E0,'RandomRanged'),(0x4D55C0,'StopMoving'),(0x6FCDB0,'AssignOrClearTargetAndNotifySpawnManager'),(0x50B730,'ControlledByHuman'),(0x5B3A00,'tableAccessor'),(0x5FB2E0,'GetAnimSpeed'),(0x41BEA0,'GetMapCoords'),(0x5657A0,'TryGetCellAt'),(0x7509E0,'VocPlayAt'),(0x4C93D0,'FrameCRC'),(0x5F5F00,'GetCellLevel'),(0x7DC720,'RaiseError'),(0x410450,'IsDirty'),(0x523340,'WhatAmI')]:
    log(det(va,nm))

# clean disasm of row4 caller region (FootClass::AI)
log('\n=== ROW4 CALLER clean disasm 0x4DAED0..0x4DAF00 ===')
log(R.dis(0x4DAED0,0x32))
log('\n=== ROW4 self-call region clean disasm 0x51BB60..0x51BB90 ===')
log(R.dis(0x51BB60,0x30))

out=str(ROOT/'lead/next_re_20261117_r14/S10_K12/EVIDENCE/BASELINE_RING1_CALLEES.txt')
Path(out).write_text('\n'.join(L)+'\n','utf-8',newline='\n')
# print ascii-safe markers only to console
for line in L:
    print(line.encode('utf-8','replace').decode('utf-8'))
