"""Verify delta: all evidence paths resolve, all entries exist in coverage, grade transitions valid, compute new proved counts."""
import csv, os
COV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
ATLAS=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
CARD=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2'
cov={}
with open(COV,encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'): cov[r['entry'].upper()]=r
atlas=set()
with open(ATLAS,encoding='utf-8') as f:
    f.readline()
    for line in f:
        p=line.split('\t')
        if p: atlas.add(p[0].upper())

delta=[]
with open(CARD+r'\coverage_delta.tsv',encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'): delta.append(r)

print('=== delta validation ===')
bad=0
for d in delta:
    e=d['entry'].upper()
    ev=os.path.join(CARD,d['evidence_path'])
    ok_ev=os.path.exists(ev) and os.path.getsize(ev)>0
    in_cov=e in cov
    old=cov[e]['grade'] if in_cov else 'MISSING'
    new=d['grade']
    ok_trans = old in ('[未证]','[静态推断]') and new=='[已证]'
    if not(ok_ev and in_cov and ok_trans): bad+=1
    print(e,'old=%-8s new=%s'%(old,new),'ev=OK' if ok_ev else 'ev=MISSING', 'in_atlas' if e in atlas else 'OUT', '' if (ok_ev and in_cov and ok_trans) else '<<<BAD')
print('bad =',bad)

# new proved counts
s11=[r for r in cov.values() if r['subsystem']=='S11']
old_proved_all=sum(1 for r in s11 if r['grade']=='[已证]')
old_proved_atlas=sum(1 for r in s11 if r['grade']=='[已证]' and r['entry'].upper() in atlas)
new_proved_all=old_proved_all+len(delta)
new_proved_atlas=old_proved_atlas+sum(1 for d in delta if d['entry'].upper() in atlas)
print('\nS11 proved whole-table: %d -> %d'%(old_proved_all,new_proved_all))
print('S11 proved atlas-denom: %d -> %d'%(old_proved_atlas,new_proved_atlas))
