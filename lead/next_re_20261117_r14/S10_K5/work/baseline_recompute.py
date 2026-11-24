#!/usr/bin/env python3
"""Read-only S10 baseline recompute. Uses unified case and column 5 (grade) only."""
from pathlib import Path
import csv,collections,hashlib,re,os,datetime
ROOT=Path(r'D:\Project\ra2-campaign-forge')
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
EXE=ROOT/'ra2youli/gamemd.exe'
SUB='S10'
def rows(p):
    with p.open('r',encoding='utf-8',newline='') as f:
        for r in csv.DictReader(f,delimiter='\t'): yield r
def norm(x): return x.strip().lower()
def named_S(r):
    n=r.get('name','').strip()
    return bool(n) and not n.startswith('sub_') and '::sub_' not in n and re.search(r'::(?:v?slot)\d+$',n) is None
sha=hashlib.sha256(EXE.read_bytes()).hexdigest().upper()
cov=[r for r in rows(COV) if r.get('subsystem','').strip().upper()==SUB]
atl={norm(r['entry']) for r in rows(ATL)}
by={norm(r['entry']):r for r in cov}
inter=sorted(set(by)&atl); outside=sorted(set(by)-atl)
ci=[by[e] for e in inter]; co=[by[e] for e in outside]
proved=sum(r['grade'].strip()=='[已证]' for r in ci)
print('READ_TIME_ISO='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat())
print('EXE_SHA256='+sha)
print('COVERAGE_PATH='+str(COV))
print('COVERAGE_MTIME_ISO='+datetime.datetime.fromtimestamp(COV.stat().st_mtime,datetime.timezone(datetime.timedelta(hours=8))).isoformat())
print('COVERAGE_SIZE='+str(COV.stat().st_size))
print('ATLAS_PATH='+str(ATL))
print('ATLAS_TOTAL_ROWS='+str(len(atl)))
print('S10_COVERAGE_ROWS='+str(len(cov)))
print('S10_ATLAS_INTERSECTION='+str(len(inter)))
print('S10_OUTSIDE_ATLAS='+str(len(outside)))
print('S10_INTERSECTION_GRADES='+repr(dict(collections.Counter(r['grade'].strip() for r in ci))))
print('S10_INTERSECTION_PROVED='+str(proved))
print('S10_INTERSECTION_PROVED_PCT='+f'{100.0*proved/len(inter):.4f}')
print('S10_INTERSECTION_NAMED_S_STRICT='+str(sum(named_S(r) for r in ci)))
print('DOD_PROVED_THRESHOLD_50PCT='+str((len(inter)+1)//2))
print('DOD_PROVED_NEED_ADDITIONAL='+str(max(0,(len(inter)+1)//2-proved)))
print('S10_OUTSIDE_ENTRIES='+','.join(e.upper() for e in outside))
for a in ['005B3A60','005B3970','005B3A10','005B3060','005B2DA0','005B2E10']:
 r=by.get(a.lower())
 print('ROW '+a+'='+('\t'.join([r['subsystem'],r['name'],r['one_line_semantics'],r['grade'],r['evidence_path']]) if r else 'NOT_FOUND'))
