#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核验：去重集是否恰好=非atlas coverage；各通道distinct计数；FUNC两类口径。"""
import os,sys,csv,collections
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,HERE)
from resid_common import COVERAGE,PROBE,OUTSIDE,ATLAS
OUT=os.path.dirname(HERE)

def load(p,col=0):
    s=set()
    with open(p,encoding="utf-8",errors="replace") as f:
        f.readline()
        for ln in f:
            if not ln.strip():continue
            t=ln.rstrip("\n").split("\t")
            try:s.add(int(t[col],16))
            except:pass
    return s
cov=load(COVERAGE);probe=load(PROBE);outside=load(OUTSIDE)
# atlas
at=set()
with open(ATLAS,encoding="utf-8",errors="replace") as f:
    h=f.readline().rstrip("\n").split("\t");hi={k:i for i,k in enumerate(h)}
    for ln in f:
        if not ln.strip():continue
        t=ln.rstrip("\n").split("\t");at.add(int(t[hi["entry"]],16))
nonatlas_cov=cov-at
print("cov=%d atlas=%d nonatlas_cov=%d outside=%d probe=%d"%(len(cov),len(at),len(nonatlas_cov),len(outside),len(probe)))

# candidates
cand={}
with open(os.path.join(OUT,"CANDIDATES_ALL.tsv"),encoding="utf-8") as f:
    for r in csv.DictReader(f,delimiter="\t"):
        cand[int(r["addr"],16)]=r["chan"]
print("candidates total:",len(cand))
# dedup
ded={}
with open(os.path.join(OUT,"DEDUP_VS_COVERAGE.tsv"),encoding="utf-8") as f:
    for r in csv.DictReader(f,delimiter="\t"):
        ded[int(r["addr"],16)]=r["excluded_reason"]
print("dedup excluded:",len(ded))
print("dedup reasons:",collections.Counter(v for v in ded.values()))
print("dedup set == nonatlas_cov?",set(ded)==nonatlas_cov, "diff extra=",len(set(ded)-nonatlas_cov),"missing=",len(nonatlas_cov-set(ded)))
# residual channel distinct
res={a:ch for a,ch in cand.items() if a not in ded}
print("residual:",len(res))
print("residual chan-distinct:",collections.Counter(ch for ch in res.values()))
# channel distinct from source_detail in candidates
cs=collections.Counter()
for a,ch in cand.items():
    for c in ch:cs[c]+=1
print("candidate chan distinct(any):",dict(cs))

# adjudication
adj=list(csv.DictReader(open(os.path.join(OUT,"RESIDUAL_ADJUDICATION.tsv"),encoding="utf-8"),delimiter="\t"))
print("adj rows:",len(adj))
print("verdicts:",collections.Counter(r["verdict"] for r in adj))
# two readings
c4b_like=0;c4a_func=0
for r in adj:
    if r["verdict"]!="FUNC":continue
    ev=r["evidence"]
    # c4a evidence: rail B c4=Y with op=55/83/81EC; check via source
    if "c4a=Y" in ev or "op=55" in ev or "op=83" in ev or "op=81" in ev:
        pass
print("FUNC by chan:",collections.Counter(r["chan"] for r in adj if r["verdict"]=="FUNC"))
