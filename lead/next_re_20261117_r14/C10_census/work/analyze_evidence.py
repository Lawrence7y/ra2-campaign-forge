#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C10 analyze evidence: what classes/known names/strings/imports appear in this slice."""
import os, json, re
from collections import Counter
ROOT = r"D:\Project\ra2-campaign-forge"
CARD = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C10_census")
D = json.load(open(os.path.join(CARD, "work", "evidence.json"), encoding="utf-8"))
F = D["funcs"]
print("n funcs:", len(F))
# vtable classes
cls = Counter()
for f in F:
    for c, slot, vt in f["vt"]:
        cls[c] += 1
print("\n== vtable classes (count of functions) ==")
for c, n in cls.most_common():
    print("  %4d  %s" % (n, c))
# self known names
print("\n== self_known names ==")
for f in F:
    if f["self_known"]:
        print("  %08X  %s" % (f["entry"], " | ".join(f["self_known"])))
# imports
print("\n== imports (first_import) ==")
imp = Counter(f["first_import"] for f in F if f["first_import"])
for k, n in imp.most_common():
    print("  %4d  %s" % (n, k))
# source files
print("\n== source files ==")
src = Counter(f["source"] for f in F if f["source"])
for k, n in src.most_common():
    print("  %4d  %s" % (n, k))
# module
print("\n== modules ==")
mod = Counter(f["module"] for f in F if f["module"])
for k, n in mod.most_common():
    print("  %4d  %s" % (n, k))
# strings keywords (top tokens)
print("\n== string samples (first 60) ==")
for f in F:
    if f["strings"]:
        print("  %08X  %s" % (f["entry"], f["strings"][:100].replace("\n"," ")))
        if sum(1 for _ in [0]) and False: pass
