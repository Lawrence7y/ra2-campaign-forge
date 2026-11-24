#!/usr/bin/env python3
"""S16-K2: FINAL independent verification — apply delta to coverage.tsv and recompute."""
import csv, os, re, math
ROOT=r"D:\Project\ra2-campaign-forge"
CARD=os.path.join(ROOT,r"lead\next_re_20261117_r14\S16-K2")
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS=os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
DELTA=os.path.join(CARD,"coverage_delta.tsv")

def load(p): return list(csv.DictReader(open(p,encoding='utf-8'),delimiter='\t'))
cov=load(COV); delta=load(DELTA)
atlas_entries=set(r['entry'].strip().upper() for r in load(ATLAS))
dmap={d['entry'].strip().upper():d for d in delta}

s16=[r for r in cov if r['subsystem'].strip()=='S16']
for r in s16:
    e=r['entry'].strip().upper()
    if e in dmap:
        r['name']=dmap[e]['name']; r['grade']=dmap[e]['grade']; r['one_line_semantics']=dmap[e]['one_line_semantics']
def ph(n): return re.fullmatch(r'sub_[0-9A-Fa-f]{8}',(n or '').strip()) is not None
def stat(rows):
    n=len(rows); nm=sum(1 for r in rows if not ph(r['name'])); pv=sum(1 for r in rows if r['grade'].strip()=='[已证]')
    return n,nm,pv
at=[r for r in s16 if r['entry'].strip().upper() in atlas_entries]
print("delta rows:",len(delta),"unique entries:",len(dmap))
print("delta subsystems all S16:",all(d['subsystem']=='S16' for d in delta))
print("delta grades legal:",all(d['grade'] in ('[已证]','[静态推断]','[未证]') for d in delta))
print("delta entries all in S16 coverage:",all(d['entry'].strip().upper() in {r['entry'].strip().upper() for r in cov if r['subsystem'].strip()=='S16'} for d in delta))
n,nm,pv=stat(at)
print(f"FINAL atlas S16: n={n} named={nm} ({nm/n*100:.2f}%) proved={pv} ({pv/n*100:.2f}%)")
print(f"  named threshold ceil(0.9*{n})={math.ceil(.9*n)}: {'PASS' if nm>=math.ceil(.9*n) else 'FAIL'}")
print(f"  proved threshold ceil(0.5*{n})={math.ceil(.5*n)}: {'PASS' if pv>=math.ceil(.5*n) else 'FAIL'}")
n,nm,pv=stat(s16)
print(f"FINAL ALL S16: n={n} named={nm} ({nm/n*100:.2f}%) proved={pv} ({pv/n*100:.2f}%)")
# check no empty name/semantics
print("empty name in delta:",[d['entry'] for d in delta if not d['name'].strip()])
print("empty semantics in delta:",[d['entry'] for d in delta if not d['one_line_semantics'].strip()])
