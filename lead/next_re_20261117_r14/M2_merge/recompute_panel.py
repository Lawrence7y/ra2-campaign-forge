# -*- coding: utf-8 -*-
"""Recompute PANEL proved_n/pct from merged coverage.tsv, atlas denominator only."""
import csv, os, sys, collections, re
sys.stdout.reconfigure(encoding="utf-8")
PROJ=r"D:\Project\ra2-campaign-forge"; ROOT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
def rd(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f:return list(csv.reader(f,delimiter="\t"))
def ne(e):
    e=e.strip().upper()
    if e.startswith("0X"):e=e[2:]
    try:return "%08X"%int(e,16)
    except:return e
atlas=set()
with open(os.path.join(PROJ,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv"),encoding="utf-8-sig") as f:
    for i,l in enumerate(f):
        if i==0:continue
        p=l.rstrip("\n").split("\t")
        if p:atlas.add(ne(p[0]))
cov=rd(os.path.join(ROOT,"COVERAGE","coverage.tsv"))[1:]
# per-subsystem: atlas_n = coverage rows whose entry in atlas; proved_n = those with [已证]
d=collections.defaultdict(lambda:collections.Counter())
for r in cov:
    e=ne(r[0])
    if e not in atlas:continue
    s=r[1].strip()
    d[s]["atlas_n"]+=1
    if r[4].strip()=="[已证]":d[s]["proved_n"]+=1
# PANEL current named_n/doctype_n (unchanged by merge) - parse from PANEL.md
panel=open(os.path.join(ROOT,"COVERAGE","PANEL.md"),encoding="utf-8").read()
cur={}
for line in panel.splitlines():
    if re.match(r"^\| S\d\d \|",line):
        p=[x.strip() for x in line.split("|")]
        # | S | atlas_n | named_n | named_pct | proved_n | proved_pct | doctype_n | ...
        s=p[1]; cur[s]=(int(p[2]),int(p[3]),p[4],int(p[5]),p[6],int(p[7]))
print("S | atlas_n | named_n | named_pct | proved_n(NEW) | proved_pct(NEW) | doctype_n | proved_n(OLD)")
tot_old=tot_new=tot_atlas=0
for s in sorted(cur):
    a,nm,np_,oldp,oldpp,dt=cur[s]
    an=d[s]["atlas_n"]; pn=d[s]["proved_n"]
    pp="%.2f"%(100.0*pn/an) if an else "0.00"
    tot_old+=oldp; tot_new+=pn; tot_atlas+=an
    print("%s | %d | %d | %s | %d | %s | %d | %d"%(s,a,nm,np_,pn,pp,dt,oldp))
print("TOTAL atlas_n=%d proved_old=%d proved_new=%d"%(tot_atlas,tot_old,tot_new))
print("TOTAL proved_pct new=%.2f old=%.2f"%(100.0*tot_new/tot_atlas,100.0*tot_old/tot_atlas))
