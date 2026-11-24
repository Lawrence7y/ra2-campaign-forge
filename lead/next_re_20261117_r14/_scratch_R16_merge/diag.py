# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
DELTA = os.path.join(ROOT, "R16_SLOTN_B1", "delta.tsv")
cov = open(COV, encoding="utf-8").read()
delta = open(DELTA, encoding="utf-8-sig").read()

def find(lines, e):
    return [l for l in lines if l.split("\t")[0].strip().upper().lstrip("0X") == e.upper()]

for e in ["0045A560", "00473BA0", "004D4B20"]:
    cl = [l for l in cov.splitlines() if l.split("\t")[0].upper() == e]
    dl = [l for l in delta.splitlines() if l.split("\t")[0].upper() == e]
    print("=== entry", e, "cov_hits", len(cl), "delta_hits", len(dl))
    c4 = cl[0].split("\t")[3]
    d4 = dl[0].split("\t")[3]
    print("cov4 len(chars)", len(c4), "has ④", ("④" in c4), "④pos", [i for i,ch in enumerate(c4) if ch=="④"])
    print("cov4 tail 120:", repr(c4[-120:]))
    print("d4 len(chars)", len(d4), "has ④", ("④" in d4))
    print("d4.startswith(cov4):", d4.startswith(cov4))
    print("suffix head:", repr(d4[len(c4):][:60]))
print("ord ④ =", ord("④"), " U+2463?")
