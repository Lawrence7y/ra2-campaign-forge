#!/usr/bin/env python3
"""S03-K2 T1: build TARGETS.tsv = coverage(subsystem==S03) ∩ function_atlas,
with case normalization (§990: atlas=lower hex, coverage=UPPER).
Computes named L/S (R14-R14), proved, and gap to 50% (97/194).
Read-only on all inputs; writes only into S03-K2 card dir.
"""
import csv, os, re

ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATL = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
OUTDIR = os.path.join(ROOT, r"lead\next_re_20261117_r14\S03-K2")
TARGETS = os.path.join(OUTDIR, "TARGETS.tsv")

def norm(e):
    e = e.strip().upper()
    # keep 8-hex uppercase form
    return e

# --- read atlas (set of normalized entries, and size map) ---
atl = {}
with open(ATL, "r", encoding="utf-8", errors="replace") as f:
    rd = csv.DictReader(f, delimiter="\t")
    for row in rd:
        e = norm(row["entry"])
        atl[e] = row
print(f"atlas data rows={len(atl)}")

# --- read coverage S03 ---
cov_s03 = []
with open(COV, "r", encoding="utf-8", errors="replace") as f:
    rd = csv.DictReader(f, delimiter="\t")
    for row in rd:
        if row["subsystem"].strip() == "S03":
            cov_s03.append(row)
print(f"coverage S03 rows (all)={len(cov_s03)}")

# --- intersect (case-normalized) ---
targets = []
for row in cov_s03:
    e = norm(row["entry"])
    if e in atl:
        targets.append((e, row, atl[e]))

# dedup by entry (coverage should be unique per entry)
seen = {}
for e, row, arow in targets:
    if e not in seen:
        seen[e] = (e, row, arow)
targets = [seen[e] for e in sorted(seen.keys(), key=lambda x: int(x, 16))]
print(f"S03 ∩ atlas (normalized) = {len(targets)}")

# --- write TARGETS.tsv ---
cols = ["entry", "size", "n_instr", "n_callers", "n_callees", "subsystem",
        "name", "one_line_semantics", "grade", "evidence_path", "n_sources", "conflict"]
with open(TARGETS, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(cols)
    for e, row, arow in targets:
        w.writerow([e, arow["size"], arow["n_instr"], arow["n_callers"], arow["n_callees"],
                    row["subsystem"], row["name"], row["one_line_semantics"], row["grade"],
                    row["evidence_path"], row["n_sources"], row["conflict"]])
print(f"wrote {TARGETS}")

# --- metrics (R14-R14 L/S named, proved, gap to 50%) ---
def is_named_L(name):
    n = name.strip()
    return n != "" and not n.startswith("sub_")

def is_class_sub(name):
    # Class::sub_XXXXXXXX self-made placeholder
    return re.search(r"::sub_[0-9A-Fa-f]{8}$", name.strip()) is not None

def is_named_S(name):
    return is_named_L(name) and not is_class_sub(name)

named_L = sum(1 for e,row,a in targets if is_named_L(row["name"]))
named_S = sum(1 for e,row,a in targets if is_named_S(row["name"]))
class_sub = sum(1 for e,row,a in targets if is_class_sub(row["name"]))
proved = sum(1 for e,row,a in targets if row["grade"].strip() == "[已证]")
static = sum(1 for e,row,a in targets if row["grade"].strip() == "[静态推断]")
unproved = sum(1 for e,row,a in targets if row["grade"].strip() == "[未证]")
N = len(targets)
thr = (N // 2) + 1 if N % 2 else N//2   # 97 for 194
# 50% gate per task = 97/194
gate = 97
gap = gate - proved

print("--- METRICS (denominator = S03∩atlas = %d) ---" % N)
print(f"named_L={named_L} ({named_L/N*100:.2f}%)")
print(f"named_S={named_S} ({named_S/N*100:.2f}%)  class_sub_placeholders={class_sub}")
print(f"proved=[已证] {proved} ({proved/N*100:.2f}%)")
print(f"static=[静态推断] {static}  unproved=[未证] {unproved}")
print(f"gate 50% = {gate}/{N}; gap to gate = {gap} more proved needed")
# show proved entries
proved_entries = [(e,row['name'],row['one_line_semantics']) for e,row,a in targets if row['grade'].strip()=='[已证]']
print("--- PROVED ENTRIES (%d) ---" % len(proved_entries))
for e,n,s in proved_entries:
    print(f"  {e}  {n}  | {s}")
