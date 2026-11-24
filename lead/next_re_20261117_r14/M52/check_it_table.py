# -*- coding: utf-8 -*-
"""Cross-check coverage against INITTERM_TABLE.tsv (3944 entries); confirm initterm-in-coverage count."""
import collections
COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ITT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_INITTERM\INITTERM_TABLE.tsv"
with open(COV, "r", encoding="utf-8-sig", newline="") as f:
    cl = f.read().split("\n")
while cl and cl[-1] == "":
    cl.pop()
cov = [ln.split("\t") for ln in cl[1:]]
cov_by_e = {r[0].upper(): r for r in cov}

with open(ITT, "r", encoding="utf-8-sig", newline="") as f:
    il = f.read().split("\n")
while il and il[-1] == "":
    il.pop()
print("INITTERM_TABLE header:", il[0])
print("INITTERM_TABLE data rows:", len(il) - 1)
# find entry column
hdr = il[0].split("\t")
print("cols:", hdr)
