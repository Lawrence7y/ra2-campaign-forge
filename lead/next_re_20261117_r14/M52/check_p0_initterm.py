# -*- coding: utf-8 -*-
"""Verify 67 new P0 entries (M50 48 + M51 19) are NOT in the 3944 initterm target set."""
COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ITT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_INITTERM\INITTERM_TABLE.tsv"
with open(COV, "r", encoding="utf-8-sig", newline="") as f:
    cl = f.read().split("\n")
while cl and cl[-1] == "":
    cl.pop()
cov = [ln.split("\t") for ln in cl[1:]]
with open(ITT, "r", encoding="utf-8-sig", newline="") as f:
    il = f.read().split("\n")
while il and il[-1] == "":
    il.pop()
hdr = il[0].split("\t")
itt = set(dict(zip(hdr, ln.split("\t")))["target"].strip().upper() for ln in il[1:])

p0 = [r for r in cov if "P0 入口闭合用" in r[3]]
print("P0 closure rows:", len(p0))
print("P0 closure rows whose entry is in initterm table:", sum(r[0].upper() in itt for r in p0))
print("P0 closure name families:", dict(__import__("collections").Counter(
    "initterm_thunk_" if r[2].startswith("initterm_thunk_") else ("sub_" if r[2].startswith("sub_") else "other")
    for r in p0)))
print("P0 closure subsystems:", dict(__import__("collections").Counter(r[1] for r in p0)))
# how many P0 closure rows are among the 22 pre-collected initterm sub_ names
print("P0 closure ∩ initterm(3944):", [r[0] for r in p0 if r[0].upper() in itt])
