#!/usr/bin/env python3
"""S16-K3 T3: recompute S16 DoD named%/proved% under L (PANEL literal) and S (semantic)
criteria, baseline and after applying my coverage_delta.tsv.
L: name non-empty and not 'sub_...' (slotN / Class::sub_ both counted as named).
S: semantic -- exclude bare sub_XXXXXXXX, Class::sub_XXXXXXXX, and Class::slotN placeholders.
"""
import csv, re, os, sys
ROOT=r"D:\Project\ra2-campaign-forge"
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS=os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
DELTA=os.path.join(ROOT,r"lead\next_re_20261117_r14\S16-K3\coverage_delta.tsv")

def load(path):
    with open(path,encoding='utf-8-sig') as f:
        return list(csv.DictReader(f,delimiter='\t'))

atlas={r['entry'].strip().upper() for r in load(ATLAS)}
cov=load(COV)

def named_L(name):
    n=(name or '').strip()
    return n!='' and not n.startswith('sub_')

RE_BARE=re.compile(r'^sub_[0-9A-Fa-f]{8}$')
RE_CLS_SUB=re.compile(r'::sub_[0-9A-Fa-f]{8}$')
RE_CLS_SLOT=re.compile(r'::slot\d+$')
def named_S(name):
    n=(name or '').strip()
    if n=='': return False
    if RE_BARE.match(n): return False
    if n.startswith('sub_'): return False
    if RE_CLS_SUB.search(n): return False
    if RE_CLS_SLOT.search(n): return False
    return True

def proved(grade): return (grade or '').strip()=='[已证]'

def stat(rows,label,verbose=False):
    n=len(rows)
    nl=sum(named_L(r['name']) for r in rows)
    ns=sum(named_S(r['name']) for r in rows)
    np=sum(proved(r['grade']) for r in rows)
    print(f"[{label}] n={n} named_L={nl} ({nl/n*100:.2f}%) named_S={ns} ({ns/n*100:.2f}%) proved={np} ({np/n*100:.2f}%)")
    if verbose:
        exL=[r['name'] for r in rows if named_L(r['name']) and not named_S(r['name'])]
        print("  L-only names (counted by L, excluded by S):", len(exL))
        from collections import Counter
        print("   ", Counter(exL).most_common(6))
    return dict(n=n,nl=nl,ns=ns,np=np)

s16=[r for r in cov if r['subsystem'].strip()=='S16']
inat=[r for r in s16 if r['entry'].strip().upper() in atlas]
outat=[r for r in s16 if r['entry'].strip().upper() not in atlas]
print(f"coverage rows={len(cov)}  S16 all={len(s16)}  S16∩atlas={len(inat)}  S16 outside atlas={len(outat)}")
base=stat(inat,"BASELINE S16∩atlas",verbose=True)
stat(outat,"S16 outside atlas")

# apply delta on top of baseline (entry -> override fields)
delta=load(DELTA) if os.path.exists(DELTA) else []
print(f"\ndelta rows={len(delta)}")
dmap={r['entry'].strip().upper():r for r in delta}
rows2=[]
for r in inat:
    d=dmap.get(r['entry'].strip().upper())
    rr=dict(r)
    if d:
        for k in ('name','one_line_semantics','grade','evidence_path'):
            if d.get(k): rr[k]=d[k]
    rows2.append(rr)
after=stat(rows2,"AFTER MY DELTA S16∩atlas",verbose=True)
# also full coverage including outside-atlas rows (with delta applied)
all2=[]
for r in s16:
    d=dmap.get(r['entry'].strip().upper())
    rr=dict(r)
    if d:
        for k in ('name','one_line_semantics','grade','evidence_path'):
            if d.get(k): rr[k]=d[k]
    all2.append(rr)
stat(all2,"AFTER MY DELTA S16 all coverage")

# threshold analysis
n=base['n']
import math
print(f"\nDoD item1 thresholds on atlas denom n={n}: named>=ceil(0.9n)={math.ceil(0.9*n)}  proved>=ceil(0.5n)={math.ceil(0.5*n)}")
print(f"  AFTER: named_S={after['ns']} -> {'PASS' if after['ns']>=math.ceil(0.9*n) else 'FAIL'}; proved={after['np']} -> {'PASS' if after['np']>=math.ceil(0.5*n) else 'FAIL'}")
print(f"  AFTER: named_L={after['nl']} -> {'PASS' if after['nl']>=math.ceil(0.9*n) else 'FAIL'}")
