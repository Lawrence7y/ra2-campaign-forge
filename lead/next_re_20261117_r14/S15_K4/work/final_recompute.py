#!/usr/bin/env python3
"""S15-K4 final recompute: live baseline + this card delta + optional K3 merge."""
from __future__ import annotations
import csv, hashlib, math, pathlib, re
ROOT=pathlib.Path(r'D:\Project\ra2-campaign-forge')
R14=ROOT/'lead/next_re_20261117_r14'
COV=R14/'COVERAGE/coverage.tsv'
ATLAS=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
K4=R14/'S15_K4/coverage_delta.tsv'
K3=R14/'S15-K3/coverage_delta.tsv'
EXE=ROOT/'ra2youli/gamemd.exe'
OUT=R14/'S15_K4/EVIDENCE/final_recompute_k4.txt'

def rows(p):
    with p.open('r',encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def unnamed(n):
    n=(n or '').strip()
    return (not n) or n.lower().startswith('sub_') or bool(re.search(r'::sub_[0-9a-fA-F]{8}$',n))
def parse_nohdr(p):
    out=[]
    for ln in p.read_text(encoding='utf-8').splitlines():
        if not ln.strip(): continue
        f=ln.split('\t')
        if len(f)<6: raise ValueError('bad delta row: '+ln)
        out.append({'entry':f[0].upper(),'subsystem':f[1],'name':f[2],'semantics':f[3],'grade':f[4],'evidence_path':f[5]})
    return out

cov=rows(COV); atlas=rows(ATLAS); ats={r['entry'].strip().lower() for r in atlas}
inter=[r for r in cov if r.get('subsystem','').strip()=='S15' and r['entry'].strip().lower() in ats]
d4={r['entry']:r for r in parse_nohdr(K4)}
d3={r['entry']:r for r in rows(K3)}
def stats(deltas):
    cur=[]
    for r in inter:
        q=dict(r)
        for d in deltas:
            if q['entry'] in d:
                q['name']=d[q['entry']]['name']; q['grade']=d[q['entry']]['grade']
        cur.append(q)
    n=len(cur); named=sum(1 for r in cur if not unnamed(r['name'])); proved=sum(1 for r in cur if r['grade'].strip()=='[已证]')
    return named,proved,n
need=math.ceil(0.9*len(inter))
b=stats([]); k4=stats([d4]); both=stats([d3,d4])
lines=[]
A=lines.append
A('S15-K4 final recompute (live disk; no card-carried counts)')
A('exe=%s bytes=%d sha256=%s'%(EXE,EXE.stat().st_size,hashlib.sha256(EXE.read_bytes()).hexdigest().upper()))
A('coverage rows=%d atlas rows=%d S15∩atlas denominator=%d'%(len(cov),len(atlas),len(inter)))
A('DoD 90%% named(S) target=%d'%need)
for label,(nm,pv,dn) in [('baseline',b),('after S15_K4 delta',k4),('after S15-K3 + S15_K4 deltas',both)]:
    A('%-32s named(S)=%d/%d (%.2f%%)  proved=%d/%d (%.2f%%)  named_shortfall=%d'%(
        label,nm,dn,100*nm/dn,pv,dn,100*pv/dn,max(0,need-nm)))
A('S15_K4 delta rows=%d: %s'%(len(d4),', '.join(sorted(d4))))
for e,r in sorted(d4.items()): A('  %s -> %s grade=%s evidence=%s'%(e,r['name'],r['grade'],r['evidence_path']))
A('S15-K3 delta rows=%d (not re-signed by S15_K4): %s'%(len(d3),', '.join(sorted(d3))))
A('NOTE: live coverage.tsv has not been merged with either delta; all deltas are card-local outputs only.')
OUT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
