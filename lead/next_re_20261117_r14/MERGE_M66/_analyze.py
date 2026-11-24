# -*- coding: utf-8 -*-
import csv, os, sys, hashlib

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"

def read_tsv(path):
    with open(path, encoding='utf-8', newline='') as f:
        r = csv.reader(f, delimiter='\t')
        rows = list(r)
    return rows

def entries_of(rows, verdict_col=2, verdict_val='PASS', entry_col=0, sub_col=1, header=True):
    start = 1 if header else 0
    out = []
    for row in rows[start:]:
        if len(row) <= max(entry_col, verdict_col):
            continue
        if row[verdict_col].strip() == verdict_val:
            out.append((row[entry_col].strip(), row[sub_col].strip() if len(row) > sub_col else ''))
    return out

audit6 = read_tsv(os.path.join(BASE, 'NAMED_PUSH_AUDIT6', 'verdict.tsv'))
audit5 = read_tsv(os.path.join(BASE, 'NAMED_PUSH_AUDIT5', 'verdict.tsv'))
d22 = read_tsv(os.path.join(BASE, 'NAMED_PUSH_S22_B2', 'delta.tsv'))
d06 = read_tsv(os.path.join(BASE, 'NAMED_PUSH_S06_B1', 'delta.tsv'))
d20 = read_tsv(os.path.join(BASE, 'NAMED_PUSH_S20_B1', 'delta.tsv'))

for name, rows in [('AUDIT6', audit6), ('AUDIT5', audit5), ('D22', d22), ('D06', d06), ('D20', d20)]:
    print(f"{name}: total rows={len(rows)} (incl header); header={rows[0]}")

pass6 = entries_of(audit6)
pass5 = entries_of(audit5)
print(f"\nAUDIT6 PASS entries = {len(pass6)}")
from collections import Counter
print("  by subsystem:", dict(Counter(s for _, s in pass6)))
print(f"AUDIT5 PASS entries = {len(pass5)}")
print("  by subsystem:", dict(Counter(s for _, s in pass5)))

def delta_entries(rows):
    return [r[0].strip() for r in rows[1:] if len(r) > 0 and r[0].strip()!='']

de22 = delta_entries(d22)
de06 = delta_entries(d06)
de20 = delta_entries(d20)
print(f"\nD22 entries={len(de22)}, D06={len(de06)}, D20={len(de20)}")

# PASS sets (by subsystem)
pass6_set = set(e for e,_ in pass6)
pass5_s06_set = set(e for e,s in pass5 if s=='S06')
pass5_s20_set = set(e for e,s in pass5 if s=='S20')

# Intersections
inter22 = [e for e in de22 if e in pass6_set]
inter06 = [e for e in de06 if e in pass5_s06_set]
inter20 = [e for e in de20 if e in pass5_s20_set]
print(f"\n=== INTERSECTION COUNTS ===")
print(f"Group A (AUDIT6 PASS ∩ D22): {len(inter22)}  (expected 18)")
print(f"Group B-S06 (AUDIT5 PASS[S06] ∩ D06): {len(inter06)}  (expected 4)")
print(f"Group B-S20 (AUDIT5 PASS[S20] ∩ D20): {len(inter20)}  (expected 7)")

# Mismatch checks: PASS not in delta, delta not in PASS
def check(name, pass_set, de):
    de_set = set(de)
    pass_not_in_delta = sorted(pass_set - de_set)
    delta_not_in_pass = sorted(de_set - pass_set)
    print(f"\n{name}: PASS not in delta = {len(pass_not_in_delta)} {pass_not_in_delta}")
    print(f"{name}: delta not in PASS = {len(delta_not_in_pass)} {delta_not_in_pass}")

check('A (AUDIT6 vs D22)', pass6_set, de22)
check('B-S06 (AUDIT5[S06] vs D06)', pass5_s06_set, de06)
check('B-S20 (AUDIT5[S20] vs D20)', pass5_s20_set, de20)

# Also check subsystem of delta entries
for name, rows in [('D22', d22), ('D06', d06), ('D20', d20)]:
    print(f"\n{name} subsystems:", dict(Counter(r[1] for r in rows[1:] if len(r)>1)))
    print(f"{name} grades:", dict(Counter(r[4] for r in rows[1:] if len(r)>4)))
