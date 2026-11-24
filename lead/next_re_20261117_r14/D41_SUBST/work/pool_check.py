# -*- coding: utf-8 -*-
"""Test which pool definition reproduces the ruling's 'S02可升262 / S19可升278'."""
import os, sys, struct
sys.path.insert(0, os.path.dirname(__file__))
from common import find_dword

COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
atlas=set()
for line in open(ATLAS, encoding="utf-8", errors="replace"):
    f=line.split("\t")
    if f and f[0]!="entry":
        try: atlas.add(f[0].strip().upper())
        except: pass

rows=[]
for line in open(COV, encoding="utf-8", errors="replace"):
    f=line.rstrip("\n").split("\t")
    if len(f)<5 or f[0]=="entry": continue
    if f[1] not in ("S02","S19"): continue
    rows.append((f[0].upper(), f[1], f[4], f[2]))

for sub in ("S02","S19"):
    rr=[r for r in rows if r[1]==sub]
    print("=== %s ==="%sub)
    print(" total",len(rr)," in_atlas",sum(1 for r in rr if r[0] in atlas))
    for label,pool in [
        ("all non-proved",[r for r in rr if r[2]!='[已证]']),
        ("[未证]+[静态推断] in atlas",[r for r in rr if r[2]!='[已证]' and r[0] in atlas]),
    ]:
        z=[r for r in pool if len(find_dword(int(r[0],16)))==0]
        print("  %-28s pool=%d noVT=%d"%(label,len(pool),len(z)))
