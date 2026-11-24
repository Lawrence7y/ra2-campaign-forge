# -*- coding: utf-8 -*-
"""Final verification: coverage invariants, PANEL consistency, file scopes."""
import csv, os, sys, collections, re
sys.stdout.reconfigure(encoding="utf-8")
ROOT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"; PROJ=r"D:\Project\ra2-campaign-forge"
COVD=os.path.join(ROOT,"COVERAGE")
def rd(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f:return list(csv.reader(f,delimiter="\t"))
def ne(e):
    e=e.strip().upper()
    if e.startswith("0X"):e=e[2:]
    try:return "%08X"%int(e,16)
    except:return e
cov=rd(os.path.join(COVD,"coverage.tsv"))
data=cov[1:]
print("coverage data rows:",len(data))
print("grades:",dict(collections.Counter(r[4] for r in data)))
print("conflict=1:",sum(1 for r in data if r[7].strip()=="1"))
print("S22:",sum(1 for r in data if r[1].strip()=="S22"))
dups=[e for e,c in collections.Counter(ne(r[0]) for r in data).items() if c>1]
print("duplicate entries:",len(dups))
# all subsystems S01-S22
bad=[r[0] for r in data if not re.match(r"^S\d\d$",r[1].strip())]
print("non-Sdd subsystems in coverage:",len(bad))
# upgrades sanity: [已证] 1125 = 1022 + 103; new rows both [已证]
# atlas proved
atlas=set()
with open(os.path.join(PROJ,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv"),encoding="utf-8-sig") as f:
    for i,l in enumerate(f):
        if i==0:continue
        p=l.rstrip("\n").split("\t")
        if p:atlas.add(ne(p[0]))
inatlas=[r for r in data if ne(r[0]) in atlas]
print("coverage rows in atlas:",len(inatlas),"atlas-proved:",sum(1 for r in inatlas if r[4].strip()=="[已证]"))
# PANEL TOTAL row
panel=open(os.path.join(COVD,"PANEL.md"),encoding="utf-8").read()
tot=[l for l in panel.splitlines() if l.startswith("| **TOTAL**")][0]
print("PANEL TOTAL:",tot)
# aux counts
for fn in ["CONFLICTS.tsv","PENDING_CORRECTIONS.tsv","probe_and_data_entries.tsv","PANEL.md"]:
    print(fn,"lines=",sum(1 for _ in open(os.path.join(COVD,fn),encoding="utf-8")))
# report lines
rp=os.path.join(ROOT,"M2_merge","REPORT.md")
print("REPORT lines=",sum(1 for _ in open(rp,encoding="utf-8")))
