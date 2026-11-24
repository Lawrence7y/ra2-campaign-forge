#!/usr/bin/env python3
"""Dump all S16 rows in atlas with names, to classify naming patterns for S/L criteria."""
import csv, re, os
ROOT=r"D:\Project\ra2-campaign-forge"
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS=os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
with open(ATLAS,encoding='utf-8') as f: atlas={r['entry'].strip().upper() for r in csv.DictReader(f,delimiter='\t')}
with open(COV,encoding='utf-8') as f: cov=list(csv.DictReader(f,delimiter='\t'))
s16=[r for r in cov if r['subsystem'].strip()=='S16']
inat=[r for r in s16 if r['entry'].strip().upper() in atlas]
print(f"coverage total rows={len(cov)}  S16 rows={len(s16)}  S16∩atlas={len(inat)}")
print(f"{'entry':10} {'grade':12} {'name'}")
for r in sorted(inat,key=lambda x:x['entry']):
    print(f"{r['entry']:10} {r['grade']:12} {r['name']}")
