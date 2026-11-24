# -*- coding: utf-8 -*-
"""Diagnose exact named criteria by finding rows that differ vs M47."""
import re
COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATL = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"

def load_cov():
    with open(COV,"r",encoding="utf-8-sig",newline="") as f:
        lines=f.read().split("\n")
    while lines and lines[-1]=="": lines.pop()
    return [ln.split("\t") for ln in lines[1:]]
def load_atl():
    with open(ATL,"r",encoding="utf-8-sig",newline="") as f:
        lines=f.read().split("\n")
    while lines and lines[-1]=="": lines.pop()
    return set(ln.split("\t")[0].strip().upper() for ln in lines[1:])

cov=load_cov(); atl=load_atl()
inatl=[r for r in cov if r[0].upper() in atl]

# collect all distinct name shapes containing ::sub_ or ::slot or ::vslot
print("=== names containing '::sub_' (all atlas) ===")
c=collections=__import__("collections").Counter
for r in inatl:
    n=r[2]
    if "::sub_" in n:
        print(f"  {r[0]} {r[1]:4} {n}")

print("\n=== S13 atlas names with slot/vslot (all) ===")
s13=[r for r in inatl if r[1].strip()=="S13"]
for r in s13:
    n=r[2]
    if re.search(r'::v?slot', n):
        print(f"  {r[0]} {n}")

print("\n=== S19 atlas names with ::sub_ ===")
s19=[r for r in inatl if r[1].strip()=="S19"]
for r in s19:
    n=r[2]
    if "::sub_" in n or re.search(r'::v?slot',n):
        print(f"  {r[0]} {n}")

print("\n=== S05 atlas names with ::sub_ ===")
s05=[r for r in inatl if r[1].strip()=="S05"]
for r in s05:
    n=r[2]
    if "::sub_" in n or re.search(r'::v?slot',n):
        pass  # too many, print only ::sub_
for r in s05:
    if "::sub_" in r[2]:
        print(f"  {r[0]} {r[2]}")
