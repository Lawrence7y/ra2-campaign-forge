#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C10 explore: confirm slice boundaries (data[11628:12916]) and basic stats."""
import os, sys
ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, "lead\\next_re_20261112_r10\\W130_atlas")
fa = os.path.join(ATLAS, "function_atlas.tsv")
lines = open(fa, encoding="utf-8", errors="replace").read().splitlines()
hdr = lines[0].split("\t")
data = [ln for ln in lines[1:] if ln.strip()]
print("hdr:", hdr)
print("data rows:", len(data))
assert len(data) == 12916
SL = data[11628:12916]
print("slice len:", len(SL))
def parse(ln):
    p = ln.split("\t"); r = dict(zip(hdr, p))
    return (int(r["entry"],16), int(r["size"]), int(r["n_instr"]), int(r["n_strings"] or 0), r["strings"], r["first_import"])
P = [parse(x) for x in SL]
lo = min(x[0] for x in P); hi = max(x[0]+x[1] for x in P)
print("lo:", hex(lo), "hi:", hex(hi))
print("first 5:")
for x in P[:5]: print("  %08X size=%d instr=%d str=%d imp=%s strs=%s" % (x[0],x[1],x[2],x[3],x[5],x[4][:60]))
print("last 5:")
for x in P[-5:]: print("  %08X size=%d instr=%d str=%d imp=%s strs=%s" % (x[0],x[1],x[2],x[3],x[5],x[4][:60]))
# previous card last entry / next boundary
prev = parse(data[11627])
print("prev(data[11627]):", hex(prev[0]), "end", hex(prev[0]+prev[1]))
# count functions with strings / import
print("with strings:", sum(1 for x in P if x[3]>0))
print("with import:", sum(1 for x in P if x[5]))
print("size==0:", sum(1 for x in P if x[1]==0))
