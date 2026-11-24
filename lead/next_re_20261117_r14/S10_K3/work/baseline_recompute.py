#!/usr/bin/env python3
"""S10-K3 on-disk baseline (S10), read-only. stdout only."""
from pathlib import Path
import csv,collections,hashlib
ROOT=Path(r'D:\Project\ra2-campaign-forge')
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
EXE=ROOT/'ra2youli/gamemd.exe'
SUB='S10'
def rows(p):
    with p.open('r',encoding='utf-8',newline='') as f:
        for r in csv.DictReader(f,delimiter='\t'): yield r
def norm(x): return x.strip().lower()
def named_L(r):
    n=r.get('name','').strip(); return bool(n) and not n.startswith('sub_')
def named_S(r):
    n=r.get('name','').strip(); return bool(n) and not n.startswith('sub_') and '::sub_' not in n
sha=hashlib.sha256(EXE.read_bytes()).hexdigest().upper()
cov=[r for r in rows(COV) if r.get('subsystem','').strip().upper()==SUB]
atl={norm(r['entry']) for r in rows(ATL)}
by={norm(r['entry']):r for r in cov}
inter=sorted(set(by)&atl); outside=sorted(set(by)-atl)
ci=[by[e] for e in inter]; co=[by[e] for e in outside]
proved=sum(r['grade'].strip()=='[已证]' for r in ci)
print('EXE_SHA256='+sha)
print('COVERAGE_TOTAL_ROWS='+str(sum(1 for _ in rows(COV))))
print('ATLAS_TOTAL_ROWS='+str(len(atl)))
print('S10_COVERAGE_ROWS='+str(len(cov)))
print('S10_ATLAS_INTERSECTION='+str(len(inter)))
print('S10_COVERAGE_OUTSIDE_ATLAS='+str(len(outside)))
print('S10_INTERSECTION_GRADES='+repr(dict(collections.Counter(r['grade'].strip() for r in ci))))
print('S10_OUTSIDE_GRADES='+repr(dict(collections.Counter(r['grade'].strip() for r in co))))
print('S10_ALL_GRADES='+repr(dict(collections.Counter(r['grade'].strip() for r in cov))))
print('S10_INTERSECTION_PROVED='+str(proved))
print('S10_INTERSECTION_NAMED_L='+str(sum(named_L(r) for r in ci)))
print('S10_INTERSECTION_NAMED_S='+str(sum(named_S(r) for r in ci)))
print('DOD_PROVED_THRESHOLD_50PCT='+str((len(inter)+1)//2))
print('DOD_PROVED_NEED_ADDITIONAL='+str(max(0,(len(inter)+1)//2-proved)))
print('DOD_PROVED_CURRENT_PCT='+(f'{100.0*proved/len(inter):.4f}' if inter else 'NA'))
print('S10_INTERSECTION_ENTRIES='+','.join(inter))
