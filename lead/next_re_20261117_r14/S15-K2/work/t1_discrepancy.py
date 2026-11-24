#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Investigate S15 row-count discrepancy: 159 in coverage vs PANEL 158; find out-of-atlas row."""
import csv, os, re
ROOT = r"D:\Project\ra2-campaign-forge"
COV  = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATL  = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
CARD = os.path.join(ROOT, r"lead\next_re_20261117_r14\S15-K2")

def read_tsv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))
def norm(e): return e.strip().upper().zfill(8)

cov = read_tsv(COV); atl = read_tsv(ATL)
atl_by = {norm(r["entry"]): r for r in atl}
s15 = [r for r in cov if r.get("subsystem","").strip()=="S15"]

def is_L(n):
    n=(n or "").strip(); return bool(n) and not n.startswith("sub_")
def is_S(n):
    n=(n or "").strip()
    return bool(n) and not n.startswith("sub_") and "::sub_" not in n

print("=== S15 rows NOT in function_atlas.tsv ===")
for r in s15:
    e=norm(r["entry"])
    if e not in atl_by:
        print(f"  {e}  name={r['name']!r}  grade={r['grade']}  src={r['n_sources']} conflict={r['conflict']}")
        print(f"     sem={r['one_line_semantics']}")
        print(f"     ev={r['evidence_path']}")

print("\n=== S15 rows in atlas (atlas口径) ===")
inat=[r for r in s15 if norm(r["entry"]) in atl_by]
print(f"  count={len(inat)}")
print(f"  L-named={sum(1 for r in inat if is_L(r['name']))}")
print(f"  S-named={sum(1 for r in inat if is_S(r['name']))}")
print(f"  proved={sum(1 for r in inat if r['grade'].strip()=='[已证]')}")

print("\n=== Duplicate entries in S15? ===")
from collections import Counter
c=Counter(norm(r["entry"]) for r in s15)
dups={k:v for k,v in c.items() if v>1}
print("  dups:", dups if dups else "none")

print("\n=== PANEL cross-check (S15 row from PANEL.md) ===")
print("  PANEL: atlas_n=158 named_n=107 proved_n=53")
print(f"  disk : atlas_n={len(inat)} L-named={sum(1 for r in inat if is_L(r['name']))} proved={sum(1 for r in inat if r['grade'].strip()=='[已证]')}")
