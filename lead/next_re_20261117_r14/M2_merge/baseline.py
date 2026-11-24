# -*- coding: utf-8 -*-
"""M2 baseline measurement — read-only. Prints exact counts to compare with the派卡基线."""
import csv, os, sys, collections

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")

def read_tsv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f, delimiter="\t"))

rows = read_tsv(COV)
header = rows[0]
data = rows[1:]
print("HEADER:", header)
print("TOTAL_LINES(incl header):", len(rows))
print("DATA_ROWS:", len(data))

# grade distribution (col index 4)
grade = collections.Counter(r[4] for r in data if len(r) > 4)
print("GRADES:")
for k in sorted(grade, key=lambda x: -grade[x]):
    print("  %s : %d" % (k, grade[k]))

# conflict=1 (col index 7)
conf1 = sum(1 for r in data if len(r) > 7 and r[7].strip() == "1")
print("CONFLICT_1:", conf1)

# S22 rows (col index 1). Note possible values like S22
s22 = sum(1 for r in data if len(r) > 1 and r[1].strip() == "S22")
print("S22_ROWS:", s22)

# subsystem distribution
sub = collections.Counter(r[1] for r in data if len(r) > 1)
print("SUBSYSTEM count:", len(sub), "sum:", sum(sub.values()))

# uniqueness of entry
entries = [r[0].strip().upper() for r in data]
dup = collections.Counter(entries)
dups = [(k,v) for k,v in dup.items() if v > 1]
print("DUPLICATE_ENTRIES:", len(dups), "extra_rows:", sum(v-1 for k,v in dups))
for k,v in dups[:20]:
    print("   DUP", k, v)

# other file line counts
for fn in ["PANEL.md","CONFLICTS.tsv","PENDING_CORRECTIONS.tsv","UNSOURCED_PROVED.tsv",
           "probe_and_data_entries.tsv","coverage_README.md","coverage_unresolved.md",
           "coverage_outside_atlas.tsv"]:
    p = os.path.join(ROOT,"COVERAGE",fn)
    with open(p,"r",encoding="utf-8-sig",newline="") as f:
        n = sum(1 for _ in f)
    print("FILE_LINES %s : %d" % (fn, n))
