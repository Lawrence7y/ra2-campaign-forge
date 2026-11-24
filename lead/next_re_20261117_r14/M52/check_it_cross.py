# -*- coding: utf-8 -*-
"""Confirm initterm-in-coverage = 3944 and B per §9.1."""
COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ITT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_INITTERM\INITTERM_TABLE.tsv"
with open(COV, "r", encoding="utf-8-sig", newline="") as f:
    cl = f.read().split("\n")
while cl and cl[-1] == "":
    cl.pop()
cov = [ln.split("\t") for ln in cl[1:]]
cov_e = set(r[0].upper() for r in cov)

with open(ITT, "r", encoding="utf-8-sig", newline="") as f:
    il = f.read().split("\n")
while il and il[-1] == "":
    il.pop()
hdr = il[0].split("\t")
rows = [dict(zip(hdr, ln.split("\t"))) for ln in il[1:]]
print("initterm table rows:", len(rows))
ti = set(r["target"].strip().upper() for r in rows)
print("unique targets:", len(ti))
print("in_coverage flag counts:", dict(__import__("collections").Counter(r["in_coverage"] for r in rows)))
print("in_atlas flag counts:", dict(__import__("collections").Counter(r["in_atlas"] for r in rows)))
# cross reference against current coverage by target
in_cov = [r for r in rows if r["target"].strip().upper() in cov_e]
print("initterm targets present in current coverage:", len(in_cov))
# those NOT named initterm_thunk_ (the 22 pre-collected)
not_thunk = [r for r in in_cov if not any(c[0].upper()==r["target"].strip().upper() and c[2].startswith("initterm_thunk_") for c in cov)]
print("initterm-in-cov whose coverage name is NOT initterm_thunk_:", len(not_thunk))
for r in not_thunk[:30]:
    ce = r["target"].strip().upper()
    c = next(c for c in cov if c[0].upper()==ce)
    print("  ", ce, c[1], c[2], c[4])
