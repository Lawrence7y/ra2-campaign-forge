#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulate merge of this card's coverage_delta.tsv into coverage.tsv and recompute
S17 named(S)/proved under R14-R14 S口径. Read-only (no writes to coverage.tsv).
"""
import csv,io,os,sys,re
ROOT=r"D:\Project\ra2-campaign-forge"
COV=os.path.join(ROOT,r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
CARD=os.path.join(ROOT,r"lead\next_re_20261117_r14\S17-K3")
DELTA=os.path.join(CARD,"coverage_delta.tsv")
ATLAS=os.path.join(ROOT,r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
def load(p):
    with io.open(p,"r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f,delimiter="\t"))
cov=load(COV)
# delta has NO header row (single data line) -> supply explicit fieldnames
DELTA_FIELDS=["entry","subsystem","name","one_line_semantics","grade","evidence_path"]
with io.open(DELTA,"r",encoding="utf-8-sig",newline="") as f:
    delta=list(csv.DictReader(f,delimiter="\t",fieldnames=DELTA_FIELDS))
atlas=load(ATLAS)
aent=set(r["entry"].lower() for r in atlas)
RANK={"[未证]":0,"[静态推断]":1,"[已证]":2}
CLASS_SUB=re.compile(r"::sub_[0-9A-Fa-f]{8}\b")
def named_S(n):
    n=(n or "").strip()
    return n!="" and not n.startswith("sub_") and not CLASS_SUB.search(n)
def stat(rows,tag):
    s=[r for r in rows if r.get("subsystem")=="S17" and r["entry"].lower() in aent]
    den=len(s)
    ns=sum(1 for r in s if named_S(r.get("name","")))
    pr=sum(1 for r in s if r.get("grade")=="[已证]")
    out.append(f"{tag}: 分母={den} named(S)={ns} ({100*ns/den:.2f}%) proved={pr} ({100*pr/den:.2f}%)")
    return den,ns,pr
out=[]
d0=stat(cov,"BEFORE")
# apply delta: for each delta entry, if grade rank higher -> replace name/grade/sem
by={r["entry"].lower():r for r in cov}
for d in delta:
    e=d["entry"].lower(); newg=d.get("grade","")
    r=by.get(e)
    if r is None:
        out.append(f"delta {d['entry']}: entry not in coverage (SKIP)");continue
    oldg=r.get("grade","")
    if RANK.get(newg,-1)>RANK.get(oldg,-1):
        r["name"]=d["name"];r["grade"]=newg;r["one_line_semantics"]=d.get("one_line_semantics","")
        out.append(f"delta {d['entry']}: APPLIED grade {oldg}->{newg}, name -> {d['name']}")
    else:
        out.append(f"delta {d['entry']}: NOT applied (new grade {newg} <= old {oldg})")
d1=stat(cov,"AFTER")
out.append(f"DELTA named(S): {d1[1]-d0[1]:+d}; proved: {d1[2]-d0[2]:+d}")
out.append(f"DoD gate: named>=90% needs 92; AFTER named(S)={d1[1]} -> {'PASS' if d1[1]>=92 else 'FAIL'}")
txt="\n".join(out)+"\n"
with io.open(os.path.join(CARD,"EVIDENCE","dod_recompute.txt"),"w",encoding="utf-8") as f:f.write(txt)
sys.stdout.write(txt)
