#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print compact listing of all S15 atlas rows grouped by grade/name class."""
import csv, os, re
ROOT = r"D:\Project\ra2-campaign-forge"
COV  = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATL  = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
def rd(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f,delimiter="\t"))
def norm(e): return e.strip().upper().zfill(8)
cov=rd(COV); atl={norm(r["entry"]):r for r in rd(ATL)}
s15=[r for r in cov if r["subsystem"].strip()=="S15" and norm(r["entry"]) in atl]

def cls(n):
    n=(n or "").strip()
    if re.match(r"^sub_[0-9A-Fa-f]{8}$",n): return "SUB"
    if "::sub_" in n: return "CSUB"
    if n=="" : return "EMPTY"
    return "NAMED"

for g in ["[已证]","[静态推断]","[未证]"]:
    rows=[r for r in s15 if r["grade"].strip()==g]
    print(f"\n######## GRADE {g}  count={len(rows)} ########")
    for r in sorted(rows,key=lambda x:norm(x["entry"])):
        e=norm(r["entry"]); a=atl[e]
        sem=r["one_line_semantics"].replace("\n"," ")[:70]
        print(f"{e} sz={a['size']:>5} nc={a['n_callers']:>4} {cls(r['name']):<5} {r['name']:<38} | {sem}")
