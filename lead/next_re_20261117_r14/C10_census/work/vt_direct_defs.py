#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对比虚表直指未收录入口的两种口径：not-in-atlas-entries vs owner()==None。"""
import os, json, bisect
ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas")
CARD = os.path.join(ROOT, "lead", "next_re_20261117_r14", "C10_census")
LO, HI = 0x773500, 0x7E038D
lines = open(os.path.join(ATLAS, "function_atlas.tsv"), encoding="utf-8", errors="replace").read().splitlines()
hdr = lines[0].split("\t"); rows = []
for ln in lines[1:]:
    if not ln.strip(): continue
    r = dict(zip(hdr, ln.split("\t"))); rows.append((int(r["entry"], 16), int(r["size"])))
rows.sort(); starts = [a for a, _ in rows]; sizes = dict(rows); es = set(starts)
def owner(x):
    i = bisect.bisect_right(starts, x) - 1
    return starts[i] if i >= 0 and starts[i] <= x < starts[i] + sizes[starts[i]] else None
ri = json.load(open(os.path.join(CARD, "work", "rtti_independent.json"), encoding="utf-8"))
slots = set()
for v in ri["vtables"]:
    for s in v["slots_list"]: slots.add(int(s, 16))
not_in = [x for x in sorted(slots) if LO <= x < HI and x not in es]
hole = [x for x in not_in if owner(x) is None]
inside = [x for x in not_in if owner(x) is not None]
print("slots total unique:", len(slots))
print("in-slice & not-in-atlas-entries:", len(not_in))
print("  owner()==None (hole):", len(hole), [hex(x) for x in hole])
print("  inside existing atlas fn body:", len(inside))
print("  inside list:", [hex(x) for x in inside][:60])
