#!/usr/bin/env python3
"""S13-K4 baseline: S13 coverage ∩ atlas, self-recompute named(L/S) + proved on disk.
Read-only on game/atlas/coverage. Writes TARGETS.tsv in this card dir.
"""
import csv, os, re, sys
ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
OUT = os.path.join(ROOT, r"lead\next_re_20261117_r14\S13_K4\TARGETS.tsv")

def norm(e):
    e = e.strip().upper()
    if e.startswith("0X"): e = e[2:]
    return e.zfill(8)

atlas = {}
with open(ATLAS, encoding="utf-8", errors="replace") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r.get("entry"): atlas[norm(r["entry"])] = r

s13 = {}
with open(COV, encoding="utf-8", errors="replace") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r.get("entry") and r.get("subsystem","").strip().upper() == "S13":
            s13[norm(r["entry"])] = r

keys = sorted(k for k in s13 if k in atlas)
CLASS_SUB = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*::sub_[0-9A-Fa-f]{8}$")
def named_L(n): return bool(n) and not n.startswith("sub_")
def named_S(n): return named_L(n) and not CLASS_SUB.match(n)

rows=[]; cL=cS=cP=0
from collections import Counter
grade_ct = Counter(); name_ct = Counter()
for k in keys:
    c=s13[k]; a=atlas[k]
    nm=c.get("name",""); g=c.get("grade","")
    L=1 if named_L(nm) else 0; S=1 if named_S(nm) else 0; P=1 if g=="[已证]" else 0
    cL+=L; cS+=S; cP+=P; grade_ct[g]+=1; name_ct[nm]+=1
    rows.append((k,a.get("size",""),a.get("n_instr",""),a.get("n_callers",""),nm,g,str(L),str(S),str(P),c.get("one_line_semantics",""),c.get("evidence_path","")))

n=len(keys)
print("S13 coverage rows:", len(s13))
print("S13 ∩ atlas:", n)
print(f"named_L={cL}/{n} ({cL/n*100:.2f}%)  named_S={cS}/{n} ({cS/n*100:.2f}%)")
print(f"proved={cP}/{n} ({cP/n*100:.2f}%)  target@50%={-(-n*50//100)}  need +{-(-n*50//100)-cP}")
print("grade distribution:", dict(grade_ct))
print("top names:", name_ct.most_common(8))

with open(OUT,"w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["entry","atlas_size","n_instr","n_callers","name","grade","named_L","named_S","proved","semantics","evidence_path"])
    for r in rows: w.writerow(r)
print("wrote", OUT)
