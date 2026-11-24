# -*- coding: utf-8 -*-
"""M76 read-only exploration: current coverage state of 7 entries, atlas membership, PANEL structure."""
import csv, os, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
EXP = ["005FEAF0","006B5850","0071CDA0","00432050","0046D000","0046D090","0071B1B0"]

def ne(e):
    e=e.strip().upper()
    if e.startswith("0X"): e=e[2:]
    try: return "%08X"%int(e,16)
    except ValueError: return e

# atlas
atlas=set()
with open(ATLAS, encoding="utf-8-sig", newline="") as f:
    rd=csv.reader(f, delimiter="\t"); hdr=next(rd)
    for r in rd:
        if r and r[0].strip(): atlas.add(ne(r[0]))
print("ATLAS header:", hdr[:4], "entries:", len(atlas))

# coverage
with open(COV,"rb") as f:
    lines=f.read().decode("utf-8").split("\n")
data=[ln.split("\t") for ln in lines[1:] if ln]
print("coverage data rows:", len(data))
full=sum(1 for r in data if r[4].strip()=="[已证]")
atl_in=sum(1 for r in data if ne(r[0]) in atlas and r[4].strip()=="[已证]")
print("full=",full,"atl_in=",atl_in,"atl_out=",full-atl_in)

by=collections.defaultdict(list)
for i,ln in enumerate(lines[1:], start=2):
    parts=ln.split("\t")
    if len(parts)==8: by[ne(parts[0])].append((i,parts))
for e in EXP:
    hits=by.get(e,[])
    print(f"\n--- {e} atlas_in={e in atlas} hits={len(hits)} ---")
    for ln,s in hits:
        print(f"  line {ln}: sub={s[1]!r} name={s[2]!r}")
        print(f"    col4[:200]={s[3][:200]!r}")
        print(f"    col4 contains 0071B1A0? {'0071B1A0' in s[3]}  007F51A0? {'007F51A0' in s[3]}  ff5110读入? {'ff 51 10' in s[3]}")
        print(f"    col5={s[4]!r} col6={s[5]!r}")

# per-subsystem baseline proved/strict for S03,S06,S16,S21
RE_CSUB=re.compile(r"::sub_[0-9A-Fa-f]+$"); RE_SLOT=re.compile(r"::v?slot\d+$")
d=collections.defaultdict(collections.Counter)
for r in data:
    e=ne(r[0]); s=r[1].strip()
    if e not in atlas: continue
    name,sem,grade=r[2].strip(),r[3],r[4].strip()
    d[s]["atlas_n"]+=1
    if name and not name.startswith("sub_"):
        d[s]["named_L"]+=1
        if not RE_CSUB.search(name):
            d[s]["named_S14"]+=1
            if not RE_SLOT.search(name): d[s]["named_strict"]+=1
    if grade=="[已证]":
        d[s]["proved"]+=1
        if "[未证]" not in sem: d[s]["strict"]+=1
print("\n=== per-subsystem baseline (atlas-in) ===")
for s in ("S03","S06","S16","S21"):
    print(f"  {s}: atlas_n={d[s]['atlas_n']} named_S14={d[s]['named_S14']} proved={d[s]['proved']} strict={d[s]['strict']}")
import math
def dod(key):
    out=[]
    for s in sorted(k for k in d if re.match(r"^S\d\d$",k)):
        a=d[s]["atlas_n"]; tn=math.ceil(0.9*a); tp=math.ceil(0.5*a)
        if d[s]["named_S14"]>=tn and d[s][key]>=tp: out.append(s)
    return out
print("  DoD nominal BEFORE:", ",".join(dod("proved")))
print("  DoD strict  BEFORE:", ",".join(dod("strict")))
