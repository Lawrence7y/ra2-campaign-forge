#!/usr/bin/env python3
"""S16-K2: list already-proved S16 rows; dump full bodies of named-not-proved slot functions."""
import sys, os, csv, bisect
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16-K2\work")
import re_lib as R
ROOT=r"D:\Project\ra2-campaign-forge"
b=R.Bin()

cov=list(csv.DictReader(open(os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv"),encoding='utf-8'),delimiter='\t'))
s16=[r for r in cov if r['subsystem'].strip()=='S16']
print("=== 42 PROVED S16 rows (name | semantics) ===")
for r in s16:
    if r['grade'].strip()=='[已证]':
        print(f"{r['entry']}  {r['name'][:55]:<55} | {r['one_line_semantics'][:75]}")

# atlas extents
arows,hdr=R.load_atlas()
atlas_sorted=sorted([(va,sz) for va,sz,_ in arows])
keys=[x[0] for x in atlas_sorted]
def extent(va):
    i=bisect.bisect_right(keys,va)-1
    if i>=0 and va<atlas_sorted[i][0]+atlas_sorted[i][1]: return atlas_sorted[i][0],atlas_sorted[i][1]
    return va,0x60

# named-not-proved slot funcs
nps=[r for r in s16 if r['grade'].strip()!='[已证]' and not r['name'].startswith('sub_')]
print("\n\n=== NAMED-NOT-PROVED slot functions full bodies ===")
for r in sorted(nps,key=lambda x:int(x['entry'],16)):
    va=int(r['entry'],16); st,sz=extent(va)
    end=st+sz
    print(f"\n--- {r['entry']} {r['name']} extent={st:08X}+{sz:#x} ---")
    insns=R.disasm_range(b,va,min(end,va+0x180),skipdata=True)
    for ins in insns:
        print("   ",R.fmt(ins))
