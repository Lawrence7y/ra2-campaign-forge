# -*- coding: utf-8 -*-
"""M71 pre-merge checks: intersection==11, preconditions, atlas in/out, strict口径."""
import csv, os, sys, re, collections, math
sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV   = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
AUDIT = os.path.join(ROOT, "NAMED_PUSH_AUDIT12", "verdict.tsv")
DELTA = os.path.join(ROOT, "NAMED_PUSH_S22_B4", "delta.tsv")
DELTA_B5 = os.path.join(ROOT, "NAMED_PUSH_S22_B5", "delta.tsv")

RE_SLOT = re.compile(r"::v?slot\d+$")
RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")
def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"): e = e[2:]
    try: return "%08X" % int(e, 16)
    except ValueError: return e

# atlas
atlas = set()
with open(ATLAS, encoding="utf-8-sig") as f:
    for i, l in enumerate(f):
        if i == 0: continue
        p = l.rstrip("\r\n").split("\t")
        if p and p[0].strip(): atlas.add(ne(p[0]))

# audit
audit = {}
audit_rows = []
with open(AUDIT, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.reader(f, delimiter="\t"))
for r in rows[1:]:
    if len(r) < 3: continue
    audit_rows.append(r)
    audit[ne(r[0])] = r[2].strip()
print("AUDIT data rows:", len(audit_rows), "verdicts:", collections.Counter(a[2].strip() for a in audit_rows))

# delta B4
delta = {}
delta_rows = []
with open(DELTA, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.reader(f, delimiter="\t"))
for r in rows[1:]:
    if len(r) < 4: continue
    delta_rows.append(r)
    delta[ne(r[0])] = r
print("DELTA B4 data rows:", len(delta_rows), "entries:", sorted(delta))

# intersection
inter = set(audit) & set(delta)
print("INTERSECTION count:", len(inter))
print("INTERSECTION entries:", sorted(inter))
print("AUDIT-only:", sorted(set(audit)-set(delta)))
print("DELTA-only:", sorted(set(delta)-set(audit)))

# B5 empty
with open(DELTA_B5, encoding="utf-8-sig", newline="") as f:
    b5 = list(csv.reader(f, delimiter="\t"))
print("B5 delta rows (incl header):", len(b5), "data rows:", len([r for r in b5[1:] if r and any(c.strip() for c in r)]))

# coverage
with open(COV, encoding="utf-8-sig", newline="") as f:
    cov = list(csv.reader(f, delimiter="\t"))
header = cov[0]
data = [r for r in cov[1:] if len(r) >= 8]
print("\nCOV header cols:", len(header), header)
print("COV data rows:", len(data))
# column widths
print("COV col-count distribution:", collections.Counter(len(r) for r in cov))

# preconditions
all_proved = sum(1 for r in data if r[4].strip() == "[已证]")
atlas_proved = sum(1 for r in data if ne(r[0]) in atlas and r[4].strip() == "[已证]")
out_proved = sum(1 for r in data if ne(r[0]) not in atlas and r[4].strip() == "[已证]")
atlas_n = sum(1 for r in data if ne(r[0]) in atlas)
print("\nPRECHECK all [已证]:", all_proved, "(expect 1591)")
print("PRECHECK atlas 内 [已证]:", atlas_proved, "(expect 1585)")
print("PRECHECK atlas 外 [已证]:", out_proved, "(expect 6)")
print("PRECHECK atlas_n:", atlas_n, "(expect 12916)")
print("PRECHECK S22 (atlas 内 proved):", sum(1 for r in data if ne(r[0]) in atlas and r[1].strip()=="S22" and r[4].strip()=="[已证]"), "(expect 98)")

# inter rows atlas in/out + current grade
print("\n--- 11 inter rows detail ---")
for e in sorted(inter):
    matched = [r for r in data if ne(r[0]) == e]
    print(e, "audit=",audit[e], "delta_name=",delta[e][2], "coverage_matches=",len(matched),
          "atlas=",e in atlas,
          "cur_grade=",matched[0][4].strip() if matched else "N/A",
          "cur_subsys=",matched[0][1].strip() if matched else "N/A",
          "new_sem_has_[未证]=", "[未证]" in delta[e][3])

# check all audit PASS
print("\nAll audit PASS:", all(v=="PASS" for v in audit.values()))
