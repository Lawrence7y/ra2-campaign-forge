#!/usr/bin/env python3
"""S11-K5 on-disk baseline recompute. Read-only; stdout only."""
from pathlib import Path
import csv, collections, hashlib
ROOT=Path(r"D:\Project\ra2-campaign-forge")
COV=ROOT/"lead/next_re_20261117_r14/COVERAGE/coverage.tsv"
ATL=ROOT/"lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv"
EXE=ROOT/"ra2youli/gamemd.exe"
SUB="S11"

def norm(x): return x.strip().lower()
def rows(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f,delimiter="\t"):
            yield r
sha=hashlib.sha256(EXE.read_bytes()).hexdigest().upper()
cov=[r for r in rows(COV) if r.get("subsystem","").strip().upper()==SUB]
atl={norm(r["entry"]) for r in rows(ATL)}
cov_by={norm(r["entry"]):r for r in cov}
inter=sorted(set(cov_by)&atl)
outside=sorted(set(cov_by)-atl)
def g(rs): return collections.Counter(r["grade"].strip() for r in rs)
def named_L(r):
    n=r.get("name","").strip(); return bool(n) and not n.startswith("sub_")
def named_S(r):
    n=r.get("name","").strip(); return bool(n) and not n.startswith("sub_") and "::sub_" not in n
ci=[cov_by[e] for e in inter]
co=[cov_by[e] for e in outside]
print("EXE_SHA256="+sha)
print("COVERAGE_TOTAL_ROWS="+str(sum(1 for _ in rows(COV))))
print("ATLAS_TOTAL_ROWS="+str(len(atl)))
print("S11_COVERAGE_ROWS="+str(len(cov)))
print("S11_ATLAS_INTERSECTION="+str(len(inter)))
print("S11_COVERAGE_OUTSIDE_ATLAS="+str(len(outside)))
print("S11_INTERSECTION_GRADES="+repr(dict(g(ci))))
print("S11_OUTSIDE_GRADES="+repr(dict(g(co))))
print("S11_ALL_GRADES="+repr(dict(g(cov))))
print("S11_INTERSECTION_PROVED="+str(sum(1 for r in ci if r["grade"].strip()=="[已证]")))
print("S11_INTERSECTION_NAMED_L="+str(sum(1 for r in ci if named_L(r))))
print("S11_INTERSECTION_NAMED_S="+str(sum(1 for r in ci if named_S(r))))
print("S11_ALL_NAMED_L="+str(sum(1 for r in cov if named_L(r))))
print("S11_ALL_NAMED_S="+str(sum(1 for r in cov if named_S(r))))
den=len(inter); pr=sum(1 for r in ci if r["grade"].strip()=="[已证]")
print("DOD_PROVED_THRESHOLD_50PCT="+str((den+1)//2))
print("DOD_PROVED_NEED_ADDITIONAL="+str(max(0,(den+1)//2-pr)))
print("DOD_PROVED_CURRENT_PCT="+(f"{100.0*pr/den:.4f}" if den else "NA"))
print("S11_INTERSECTION_ENTRIES="+",".join(inter))
