"""
S11-K2 T5 final: rebuild coverage_delta.tsv conservatively.
Only S11 rows that exist in coverage.tsv with grade [静态推断] or [未证],
and that have byte-hard evidence in this card's EVIDENCE/ files.
GetSize x11 (11/11 closure) + class ctors x2 (S11 only).
"""
import csv, os
COV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
CARD=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2'
ATLAS=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'

cov={}
with open(COV,encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'): cov[r['entry'].upper()]=r
atlas=set()
with open(ATLAS,encoding='utf-8') as f:
    f.readline()
    for line in f:
        p=line.split('\t')
        if p: atlas.add(p[0].upper())

# (entry, name, semantics, grade, evidence)
DELTA=[]
gets=[
('004B4CF0','DriveLocomotionClass::GetSize','off0(IPersistStream) vtable slot9: B8 70 00 00 00 C3 => 0x70; factory 6C4010 push 0x70 (6A imm8) -> new 7C8E17 closes','EVIDENCE/fresh_closure.txt'),
('004B66E0','DropPodLocomotionClass::GetSize','off0 slot9 B8 30..C3=0x30; factory 6C4910 push 0x30 (6A30) closes','EVIDENCE/fresh_closure.txt'),
('004D0390','FlyLocomotionClass::GetSize','off0 slot9 B8 60..C3=0x60; factory 6C4A90 push 0x60 (6A60) closes','EVIDENCE/fresh_closure.txt'),
('005172B0','HoverLocomotionClass::GetSize','off0 slot9 B8 78..C3=0x78; factory 6C4310 push 0x78 (6A78) closes','EVIDENCE/fresh_closure.txt'),
('0054DF90','JumpjetLocomotionClass::GetSize','off0 slot9 B8 98..C3=0x98; factory 6C4190 push 0x98 (68 imm32) closes','EVIDENCE/fresh_closure.txt'),
('005B1B40','MechLocomotionClass::GetSize','off0 slot9 B8 34..C3=0x34; factory 6C4D90 push 0x34 (6A34) closes','EVIDENCE/fresh_closure.txt'),
('006635B0','RocketLocomotionClass::GetSize','off0 slot9 B8 60..C3=0x60; factory 6C4490 push 0x60 (6A60) closes','EVIDENCE/fresh_closure.txt'),
('006A42A0','ShipLocomotionClass::GetSize','off0 slot9 B8 70..C3=0x70; factory 6C4F10 push 0x70 (6A70) closes','EVIDENCE/fresh_closure.txt'),
('0071A120','TeleportLocomotionClass::GetSize','off0 slot9 B8 4C..C3=0x4C; factory 6C4C10 push 0x4C (6A4C) closes','EVIDENCE/fresh_closure.txt'),
('0072A200','TunnelLocomotionClass::GetSize','off0 slot9 B8 3C..C3=0x3C; factory 6C4610 push 0x3C (6A3C) closes','EVIDENCE/fresh_closure.txt'),
('0075CBD0','WalkLocomotionClass::GetSize','off0 slot9 B8 3C..C3=0x3C; factory 6C4790 push 0x3C (6A3C) closes','EVIDENCE/fresh_closure.txt'),
]
for e,n,s,ev in gets: DELTA.append((e,n,s,'[已证]',ev))
ctors=[
('004AF540','DriveLocomotionClass::DriveLocomotionClass','ctor installs canonical off0=7E7F7C/off4=7E7EB0 (004AF5C2/5C8); called by factory CreateInstance 6C4010 after new(0x70)','EVIDENCE/fresh_closure.txt'),
('004B5AB0','DropPodLocomotionClass::DropPodLocomotionClass','ctor installs canonical off0=7E8344/off4=7E8278 (004B5ADD/E3); called by factory 6C4910 after new(0x30)','EVIDENCE/fresh_closure.txt'),
]
for e,n,s,ev in ctors: DELTA.append((e,n,s,'[已证]',ev))

# ---- validate ----
print('=== delta validation ===')
bad=0
rows_out=[]
for e,n,s,g,ev in DELTA:
    r=cov.get(e)
    evp=os.path.join(CARD,ev)
    ok_ev=os.path.isfile(evp) and os.path.getsize(evp)>0
    in_cov = r is not None
    sub_ok = in_cov and r['subsystem']=='S11'
    trans = in_cov and r['grade'] in ('[未证]','[静态推断]') and g=='[已证]'
    good = ok_ev and sub_ok and trans
    if not good: bad+=1
    print(e,'old=%s/%s'%(r['grade'],r['subsystem']) if in_cov else 'MISSING', 'ev=%s'%('OK' if ok_ev else 'MISS'), 'atlas=%s'%('Y' if e in atlas else 'N'), '' if good else '<<<BAD')
    rows_out.append((e,'S11',n,s,g,ev))
print('bad =',bad)

with open(CARD+r'\coverage_delta.tsv','w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n')
    w.writerow(['entry','subsystem','name','one_line_semantics','grade','evidence_path'])
    for row in rows_out: w.writerow(row)
print('\nwrote coverage_delta.tsv (%d rows)'%len(rows_out))

# ---- counts ----
s11=[r for r in cov.values() if r['subsystem']=='S11']
old_all=sum(1 for r in s11 if r['grade']=='[已证]')
old_atlas=sum(1 for r in s11 if r['grade']=='[已证]' and r['entry'].upper() in atlas)
in_atlas_delta=sum(1 for e,*_ in DELTA if e in atlas)
print('\nS11 proved ALL-table: %d -> %d'%(old_all,old_all+len(DELTA)))
print('S11 proved atlas-denom: %d -> %d (+%d rows in atlas)'%(old_atlas,old_atlas+in_atlas_delta,in_atlas_delta))
