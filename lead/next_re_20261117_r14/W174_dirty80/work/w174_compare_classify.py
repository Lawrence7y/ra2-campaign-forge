#!/usr/bin/env python3
"""Compare heuristic vs CFG classification; list disagreements."""
import os
HERE=os.path.dirname(os.path.abspath(__file__))
def load(p):
    d={}
    with open(os.path.join(HERE,"..","EVIDENCE",p),"r",encoding="utf-8") as f:
        hdr=f.readline().rstrip("\n").split("\t")
        for line in f:
            parts=line.rstrip("\n").split("\t")
            r=dict(zip(hdr,parts)); d[r["va"]]=r
    return d
h=load("w174_classify_results.tsv")
c=load("w174_classify_cfg.tsv")
print("heuristic vs CFG disagreements:")
n=0
for va in sorted(set(h)|set(c)):
    hc=h.get(va,{}).get("cls","?"); cc=c.get(va,{}).get("cls","?")
    if hc!=cc:
        n+=1
        print("  %s heuristic=%s cfg=%s  fn=%s base=%s gating=%s" % (
            va,hc,cc,c.get(va,{}).get("fn",""),c.get(va,{}).get("base",""),
            c.get(va,{}).get("gating_jcc","")))
print("total disagreements:",n)
