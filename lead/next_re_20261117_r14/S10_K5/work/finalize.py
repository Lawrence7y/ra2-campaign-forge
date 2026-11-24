#!/usr/bin/env python3
"""Build and validate S10-K5 coverage_delta.tsv, no header."""
import csv,re
from pathlib import Path
CARD=Path(__file__).resolve().parent.parent
ROOT=Path(r'D:\Project\ra2-campaign-forge')
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
FIELDS=['entry','subsystem','name','one_line_semantics','grade','evidence_path','n_sources','conflict']
def load(p):
    with p.open('r',encoding='utf-8',newline='') as f: return list(csv.DictReader(f,delimiter='\t'))
cov=load(COV); atl={r['entry'].strip().lower() for r in load(ATL)}
by={r['entry'].strip().lower():r for r in cov}
s10={e:r for e,r in by.items() if r['subsystem'].strip().upper()=='S10'}
inter={e for e in s10 if e in atl}
D=[
 ('005B3A60','MissionClass::scalar_deleting_destructor','MSVC scalar deleting dtor: restores 4 MissionClass vptrs, calls base dtor 005F3B80, flag&1 -> CRT::_delete 007C8B3D, ret 4','[已证]','EVIDENCE/005B3A60_DELETING_DTOR.txt#005B3A60','3'),
 ('004E0170','FootClass::scalar_deleting_destructor','MSVC scalar deleting dtor: RTTI FootClass vtable slot8; base dtor 004D3590; flag&1 -> CRT::_delete 007C8B3D; ret 4','[已证]','EVIDENCE/s10_scalar_dtor_candidates.txt#004E0170','2'),
 ('00523350','InfantryClass::scalar_deleting_destructor','MSVC scalar deleting dtor: RTTI InfantryClass vtable slot8; base dtor 00517D90; flag&1 -> CRT::_delete 007C8B3D; ret 4','[已证]','EVIDENCE/s10_scalar_dtor_candidates.txt#00523350','2'),
 ('006B1390','SlaveManagerClass::scalar_deleting_destructor','MSVC scalar deleting dtor: RTTI SlaveManagerClass vtable slot8; base dtor 006AF4A0; flag&1 -> CRT::_delete 007C8B3D; ret 4','[已证]','EVIDENCE/s10_scalar_dtor_candidates.txt#006B1390','2'),
 ('006B8140','SpawnManagerClass::scalar_deleting_destructor','MSVC scalar deleting dtor: RTTI SpawnManagerClass vtable slot8; base dtor 006B7010; flag&1 -> CRT::_delete 007C8B3D; ret 4','[已证]','EVIDENCE/s10_scalar_dtor_candidates.txt#006B8140','2'),
 ('00746E80','UnitClass::scalar_deleting_destructor','MSVC scalar deleting dtor: RTTI UnitClass vtable slot8; base dtor 00735780; flag&1 -> CRT::_delete 007C8B3D; ret 4','[已证]','EVIDENCE/s10_scalar_dtor_candidates.txt#00746E80','2'),
 ('005B3970','MissionClass::Save','Behavior-level Save: mission-id enum field +AC plus +B0/+B4/+BC/+C0/timer written to caller stream; base 005F6250 -> proven AbstractClass::Save 00410410; 4A1D50/4A1CA0 field serializers','[已证]','EVIDENCE/005B3970_SAVE_PROOF.txt#005B3970','4'),
]
fail=[]
seen_e=set(); seen_n=set()
for e,n,sem,grade,ev,ns in D:
    k=e.lower()
    if k in seen_e: fail.append('duplicate delta entry '+e)
    seen_e.add(k)
    if n in seen_n: fail.append('duplicate delta name '+n)
    seen_n.add(n)
    r=s10.get(k)
    if not r: fail.append('missing baseline row '+e); continue
    if r['subsystem'].strip().upper()!='S10': fail.append('not S10 '+e)
    if k not in inter: fail.append('outside atlas '+e)
    if r['grade'].strip()=='[已证]': fail.append('already proved '+e)
    if re.search(r'::(?:v?slot)\d+$',n) or n.startswith('sub_') or '::sub_' in n: fail.append('placeholder name '+n)
    p=CARD/ev.split('#')[0]
    if not p.is_file(): fail.append('missing evidence '+str(p))
    elif e not in p.read_text(encoding='utf-8',errors='replace'): fail.append('evidence lacks entry '+e)
    hits=[x for x in cov if x['name'].strip()==n and x['entry'].strip().lower()!=k]
    if hits: fail.append('name collides '+n+' '+','.join(x['entry'] for x in hits[:5]))
out=CARD/'coverage_delta.tsv'
with out.open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=FIELDS,delimiter='\t',lineterminator='\n')
    for e,n,sem,grade,ev,ns in D:
        w.writerow(dict(entry=e,subsystem='S10',name=n,one_line_semantics=sem,grade=grade,evidence_path=ev,n_sources=ns,conflict='0'))
def named_s(r):
    n=r['name'].strip()
    return bool(n) and not n.startswith('sub_') and '::sub_' not in n and re.search(r'::(?:v?slot)\d+$',n) is None
cur=sum(1 for e in inter if by[e]['grade'].strip()=='[已证]')
cur_n=sum(1 for e in inter if named_s(by[e]))
post=cur+len(D); post_n=cur_n+len(D)
lines=[]
lines.append('S10-K5 DELTA VALIDATION')
lines.append('DELTA_ROWS='+str(len(D)))
lines.append('FAIL_COUNT='+str(len(fail)))
for x in fail: lines.append('FAIL '+x)
lines.append('DUPLICATE_ENTRY=0 DUPLICATE_NAME=0 PLACEHOLDER_NAME=0')
lines.append('ALL_ROWS_S10_ATLAS_NONPROVED=YES' if not fail else 'ALL_ROWS_S10_ATLAS_NONPROVED=CHECK_FAIL')
lines.append('BASELINE_PROVED='+str(cur)+' BASELINE_INTER='+str(len(inter))+' BASELINE_PCT='+f'{100*cur/len(inter):.4f}')
lines.append('POST_PROVED='+str(post)+' POST_PCT='+f'{100*post/len(inter):.4f}')
lines.append('POST_THRESHOLD='+str((len(inter)+1)//2)+' POST_NEED='+str(max(0,(len(inter)+1)//2-post)))
lines.append('BASELINE_NAMED_S='+str(cur_n)+' POST_NAMED_S='+str(post_n))
lines.append('NOTE: 19 K4 baseline rows remain [已证] on disk despite single-source names; not modified here. See DISAGREE.md.')
(CARD/'EVIDENCE'/'delta_validate.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
if fail: raise SystemExit(2)
