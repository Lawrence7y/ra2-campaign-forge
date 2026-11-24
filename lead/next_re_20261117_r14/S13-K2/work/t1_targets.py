#!/usr/bin/env python3
"""T1: S13 targets = coverage(subsystem==S13) ∩ function_atlas.
Self-recompute named(L/S) and proved on-disk; do NOT trust card-face numbers.
Read-only on inputs. Writes TARGETS.tsv in card dir only.
"""
import csv, os, re

ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
OUT = os.path.join(ROOT, r"lead\next_re_20261117_r14\S13-K2\TARGETS.tsv")

def norm(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    return e.zfill(8)

# atlas entries
atlas = {}
with open(ATLAS, encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        if not row.get("entry"):
            continue
        atlas[norm(row["entry"])] = row
print("atlas rows:", len(atlas))

# coverage subsystem == S13
s13 = {}
all_cov = 0
with open(COV, encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        if not row.get("entry"):
            continue
        all_cov += 1
        if row.get("subsystem", "").strip().upper() == "S13":
            s13[norm(row["entry"])] = row
print("coverage rows:", all_cov, " S13 rows:", len(s13))

# intersection
keys = sorted(k for k in s13 if k in atlas)
print("S13 ∩ atlas:", len(keys))

CLASS_SUB = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*::sub_[0-9A-Fa-f]{8}$")
def named_L(name):
    return bool(name) and not name.startswith("sub_")
def named_S(name):
    return named_L(name) and not CLASS_SUB.match(name)

hcL = hcS = proved = 0
rows = []
for k in keys:
    c = s13[k]; a = atlas[k]
    nm = c.get("name", "")
    g = c.get("grade", "")
    L = 1 if named_L(nm) else 0
    S = 1 if named_S(nm) else 0
    P = 1 if g == "[已证]" else 0
    hcL += L; hcS += S; proved += P
    rows.append((k, a.get("size",""), a.get("n_instr",""), a.get("n_callers",""),
                 nm, g, str(L), str(S), str(P), c.get("one_line_semantics","")))

n = len(keys)
print(f"named_L = {hcL}/{n} = {hcL/n*100:.2f}%")
print(f"named_S = {hcS}/{n} = {hcS/n*100:.2f}%  (Class::sub_ count = {hcL-hcS})")
print(f"proved  = {proved}/{n} = {proved/n*100:.2f}%")
need_named = -(-(90*n)//100)   # ceil(0.90*n)
need_proved = -(-(50*n)//100)  # ceil(0.50*n)
print(f"named@90% target={need_named}, need +{need_named-hcS}")
print(f"proved@50% target={need_proved}, need +{need_proved-proved}")

with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["entry","atlas_size","n_instr","n_callers","name","grade","named_L","named_S","proved","semantics"])
    for r in rows:
        w.writerow(r)
print("wrote", OUT)
