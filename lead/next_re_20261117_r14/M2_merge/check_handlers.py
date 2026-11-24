# -*- coding: utf-8 -*-
"""Check S18 handler addresses vs atlas/alignment, and dump existing probe table keys."""
import csv, os, sys, glob, re
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
PROJ = r"D:\Project\ra2-campaign-forge"
def rd(p,delim="\t"):
    with open(p,"r",encoding="utf-8-sig",newline="") as f: return list(csv.reader(f,delimiter=delim))
def ne(e):
    e=e.strip().upper().replace("0X","")
    try: return "%08X"%int(e,16) if len(e)<=8 and all(c in "0123456789ABCDEF" for c in e) else e
    except: return e
# atlas
ap=os.path.join(PROJ,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
print("ATLAS exists:",os.path.exists(ap))
atlas=set()
if os.path.exists(ap):
    with open(ap,encoding="utf-8-sig") as f:
        for i,line in enumerate(f):
            if i==0: continue
            p=line.split("\t")
            if p: atlas.add(ne(p[0]))
# S18 handlers
s18=os.path.join(ROOT,"S18-F1","coverage_delta.tsv")
rows=rd(s18)
if rows[0][0].strip().lower()=="entry": rows=rows[1:]
print("\nS18 handler addresses: aligned? in atlas?")
for r in rows:
    e=ne(r[0]); a=int(e,16)
    print("  %s aligned16=%s in_atlas=%s name=%s"%(e, a%16==0, e in atlas, r[2]))
print("\n0x414B9E in atlas:", "00414B9E" in atlas, " aligned16=",int("414B9E",16)%16==0)
print("0x006CD70C in atlas:", "006CD70C" in atlas, " aligned16=",int("006CD70C",16)%16==0)
print("0x006C41D0 in atlas:", "006C41D0" in atlas, " aligned16=",int("006C41D0",16)%16==0)
print("0x005B3740 in atlas:", "005B3740" in atlas, " aligned16=",int("005B3740",16)%16==0)

# probe table existing keys
pp=os.path.join(ROOT,"COVERAGE","probe_and_data_entries.tsv")
pr=rd(pp)
print("\nPROBE header:",pr[0])
pkeys=set()
for r in pr[1:]:
    if not r or not r[0].strip(): continue
    pkeys.add(ne(r[0]))
print("PROBE distinct entries:",len(pkeys))
for k in sorted(pkeys): print("   ",k)

# coverage row for 4C6CB0, 4C9150
cov={ne(r[0]):r for r in rd(os.path.join(ROOT,"COVERAGE","coverage.tsv"))[1:]}
for e in ["004C6CB0","004C9150","00414B9E","006CDE44","004824D4"]:
    print("\nCOV %s: %s"%(e, cov.get(e,"NOT IN COV")))
