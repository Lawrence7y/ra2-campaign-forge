#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-ADJ5 step1: recompute the three dedup numbers from disk (no stale card numbers).
ENUM.tsv  : 10 TAB columns; verdict in col index 2.
coverage.tsv: header comma, data TAB; entry in col index 0.
Intersection: uppercase(entry).
"""
import csv, sys, hashlib
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
ENUM = ROOT / r"lead\next_re_20261117_r14\P0_RESIDUAL_2\ENUM.tsv"
COV  = ROOT / r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv"

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1<<20), b''):
            h.update(b)
    return h.hexdigest().upper()

# --- read ENUM ---
enum_rows = []
with open(ENUM, 'r', encoding='utf-8-sig', newline='') as f:
    r = csv.reader(f, delimiter='\t')
    header = next(r)
    for row in r:
        if not row or not row[0].strip():
            continue
        enum_rows.append(row)

from collections import Counter
verdicts = Counter(row[2].strip() for row in enum_rows if len(row) > 2)
undecidable = [row for row in enum_rows if len(row) > 2 and row[2].strip() == 'UNDECIDABLE']

# --- read coverage entries (uppercase set) ---
cov_entries = set()
cov_rows = 0
with open(COV, 'r', encoding='utf-8-sig', newline='') as f:
    lines = f.read().splitlines()
# header line uses commas, but entry is still first field up to first comma/tab
for ln in lines:
    if not ln.strip():
        continue
    # data rows: split by tab; header row split by comma (skip it via first token == 'entry')
    parts = ln.split('\t')
    token = parts[0].split(',')[0].strip()
    if token.upper() == 'ENTRY':
        continue
    cov_rows += 1
    cov_entries.add(token.upper())

und_addr = [row[0].strip().upper() for row in undecidable]
in_cov = [a for a in und_addr if a in cov_entries]
not_in_cov = [a for a in und_addr if a not in cov_entries]

# duplicates within UNDECIDABLE addresses?
dup_und = len(und_addr) - len(set(und_addr))
# is not_in_cov unique?
dup_not = len(not_in_cov) - len(set(not_in_cov))

print("ENUM data rows      :", len(enum_rows))
print("verdict distribution:", dict(verdicts))
print("UNDECIDABLE total   :", len(undecidable))
print("coverage data rows  :", cov_rows)
print("coverage distinct   :", len(cov_entries))
print("UNDECIDABLE in cov  :", len(in_cov))
print("UNDECIDABLE NOT cov :", len(not_in_cov))
print("dup UNDECIDABLE addr:", dup_und)
print("dup not-in-cov addr :", dup_not)
print("sha256 ENUM         :", sha(ENUM))
print("sha256 coverage     :", sha(COV))

# Lead's independent numbers
LEAD = (5598, 3929, 1669)
mine = (len(undecidable), len(in_cov), len(not_in_cov))
print("LEAD                :", LEAD)
print("MINE                :", mine)
print("MATCH               :", mine == LEAD)

# dump not-in-cov list sorted by address ascending for step2
out = ROOT / r"lead\next_re_20261117_r14\P0_ADJ5\work\undecidable_not_in_cov.tsv"
with open(out, 'w', encoding='utf-8', newline='') as f:
    for a in sorted(set(not_in_cov)):
        f.write(a + '\n')
print("wrote", out, "lines", len(set(not_in_cov)))
