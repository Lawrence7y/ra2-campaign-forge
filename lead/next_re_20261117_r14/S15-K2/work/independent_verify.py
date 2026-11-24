#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""INDEPENDENT final verification: recompute S15 counts from disk coverage + delta from scratch."""
import csv,os,re
ROOT=r"D:\Project\ra2-campaign-forge"
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATL=os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
CARD=os.path.join(ROOT,r"lead\next_re_20261117_r14\S15-K2")
def rd(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f,delimiter="\t"))
def norm(e): return e.strip().upper().zfill(8)
cov=rd(COV); atl=set(norm(r["entry"]) for r in rd(ATL))
# coverage_delta.tsv has NO header (first line is data)
def rd_noheader(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f:
        return [dict(zip(["entry","subsystem","name","sem","grade","ev"],line.rstrip("\n").split("\t")))
                for line in f if line.strip()]
delta=rd_noheader(os.path.join(CARD,"coverage_delta.tsv"))
print("delta rows:",len(delta))
# check all delta entries are S15, in atlas, and grade [已证]
bad=[r for r in delta if r["subsystem"]!="S15" or norm(r["entry"]) not in atl or r["grade"]!="[已证]"]
print("bad delta rows:",len(bad),[(r["entry"],r["subsystem"],r["grade"]) for r in bad])
dentries=set(norm(r["entry"]) for r in delta)
# baseline S15 atlas
s15=[r for r in cov if r["subsystem"].strip()=="S15" and norm(r["entry"]) in atl]
print("baseline S15 atlas:",len(s15))
bproved=sum(1 for r in s15 if r["grade"].strip()=="[已证]")
def named(n):
    n=(n or "").strip(); return bool(n) and not n.startswith("sub_") and "::sub_" not in n
bnamed=sum(1 for r in s15 if named(r["name"]))
# new names from delta that were sub_ before
by={norm(r["entry"]):r for r in s15}
new_named_added=0; new_proved_added=0
for d in delta:
    e=norm(d["entry"]); r=by.get(e)
    if not r: print("  WARN delta entry not in S15 atlas:",e); continue
    if r["grade"].strip()!="[已证]": new_proved_added+=1
    if not named(r["name"]) and named(d["name"]): new_named_added+=1
print(f"baseline proved={bproved} named={bnamed}")
print(f"added proved={new_proved_added} named={new_named_added}")
print(f"FINAL proved={bproved+new_proved_added}/158={(bproved+new_proved_added)/158*100:.2f}%")
print(f"FINAL named={bnamed+new_named_added}/158={(bnamed+new_named_added)/158*100:.2f}%")
# duplicate entries in delta
from collections import Counter
c=Counter(norm(r["entry"]) for r in delta)
print("duplicate delta entries:",{k:v for k,v in c.items() if v>1})
# duplicate new names
cn=Counter(r["name"] for r in delta)
print("repeated new names in delta:",{k:v for k,v in cn.items() if v>1})
