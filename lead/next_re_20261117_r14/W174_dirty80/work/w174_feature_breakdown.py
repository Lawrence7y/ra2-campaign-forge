#!/usr/bin/env python3
"""Break down classification feature triggers. For (b) sites, determine whether
gated by a real conditional jump (gate_over/gate_target) or only by a nearby cmp."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
rows=[]
with open(os.path.join(HERE,"..","EVIDENCE","w174_classify_results.tsv"),"r",encoding="utf-8") as f:
    hdr=f.readline().rstrip("\n").split("\t")
    for line in f:
        rows.append(dict(zip(hdr,line.rstrip("\n").split("\t"))))
from collections import Counter
breakdown=Counter()
for r in rows:
    if r["cls"]!="b": continue
    go=bool(r["gate_over"].strip()); gt=bool(r["gate_target"].strip()); cm=bool(r["cmps"].strip())
    key=("gate_over" if go else "")+("+gate_target" if gt else "")+("+cmps" if cm else "")
    breakdown[key]+=1
print("(b) trigger breakdown:")
for k,v in sorted(breakdown.items(), key=lambda x:-x[1]):
    print("  %-40s %d" % (k or "NONE", v))
# list b sites that are ONLY cmps (weak)
weak=[r for r in rows if r["cls"]=="b" and not r["gate_over"].strip() and not r["gate_target"].strip() and r["cmps"].strip()]
print("\n(b) sites triggered ONLY by nearby cmp (weak), count=%d:" % len(weak))
for r in weak:
    print("  %s fn=%s base=%s cmps=%s" % (r["va"],r["fn"],r["base"],r["cmps"]))
# also b sites with NO feature at all (shouldn't happen)
none=[r for r in rows if r["cls"]=="b" and not r["gate_over"].strip() and not r["gate_target"].strip() and not r["cmps"].strip()]
print("\n(b) sites with NO feature: %d" % len(none))
