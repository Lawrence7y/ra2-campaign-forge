#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 2 verification — read-only."""
import re, os, json
BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R72_T1_CLEANSCALE"
A = os.path.join(BASE,"files_tier_A_snap2.tsv"); C=os.path.join(BASE,"files_tier_C.tsv")
def load(p):
    rows=[]
    with open(p,encoding="utf-8") as fh:
        fh.readline()
        for line in fh:
            f=line.rstrip("\n").split("\t"); rows.append((f[0],int(f[2]),f[4] if len(f)>4 else ""))
    return rows
RA, RC = load(A), load(C)
def base(r): return r.rsplit("/",1)[-1]
def low(r): return base(r).lower()

print("-- REPORT.md variants --")
for label, pred in [
 ("== REPORT.md case-sensitive", lambda r: base(r)=="REPORT.md"),
 ("== report.md case-insensitive", lambda r: low(r)=="report.md"),
 ("endswith REPORT.md (any case)", lambda r: low(r).endswith("report.md")),
]:
    ha=[(r,b) for r,b,_ in RA if pred(r)]; hc=[(r,b) for r,b,_ in RC if pred(r)]
    print(f"  {label}: A={len(ha)}/{sum(b for _,b in ha)}  C={len(hc)}/{sum(b for _,b in hc)}")

print("\n-- EVIDENCE variants on C --")
for label, pred in [
 ("segment == EVIDENCE", lambda r: "EVIDENCE" in r.split("/")[:-1]),
 ("substring EVIDENCE in path", lambda r: "EVIDENCE" in r),
 ("segment startswith EVIDENCE", lambda r: any(s.startswith("EVIDENCE") for s in r.split("/")[:-1])),
]:
    hc=[(r,b) for r,b,_ in RC if pred(r)]
    print(f"  {label}: C={len(hc)}/{sum(b for _,b in hc)}")

print("\n-- 33.7MB / 50x claim --")
outj=sum(b for r,b,_ in RC if low(r).endswith("_out.json"))
so=sum(b for r,b,_ in RC if "stdout" in low(r) or "stderr" in low(r))
print(f"  out.json={outj}, stdout/stderr={so}, sum={outj+so}")
fp=262195
print(f"  sum/262195 = {(outj+so)/fp:.2f}   (claimed 50x)")

print("\n-- read JSON manifests --")
for name in ["rollback_extra.json","band_c_wide.json","probe_prior.json","q2q3_final.json","summary_snap2.json"]:
    p=os.path.join(BASE,name)
    try:
        d=json.load(open(p,encoding="utf-8"))
        print(f"  === {name} ===")
        s=json.dumps(d,ensure_ascii=False,indent=1)
        print(s[:2600])
    except Exception as e:
        print(f"  {name}: ERR {e}")

print("\n-- drift summary --")
for name in ["q2q3q4_summary.tsv","summary.tsv"]:
    p=os.path.join(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R75_T2_DRIFT",name)
    print(f"  === {name} ===")
    print(open(p,encoding="utf-8").read()[:2000])
