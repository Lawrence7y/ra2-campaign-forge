#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T1: filter coverage.tsv subsystem==S15, join function_atlas.tsv, compute L/S口径 counts.
Read-only on source files. Writes only into S15-K2 card dir.
"""
import csv, os, re, sys, json

ROOT = r"D:\Project\ra2-campaign-forge"
COV  = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATL  = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
CARD = os.path.join(ROOT, r"lead\next_re_20261117_r14\S15-K2")

def read_tsv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

cov = read_tsv(COV)
atl = read_tsv(ATL)

# normalize entry to uppercase hex8
def norm(e):
    return e.strip().upper().zfill(8)

atl_by = {}
for r in atl:
    atl_by[norm(r["entry"])] = r

s15 = [r for r in cov if r.get("subsystem", "").strip() == "S15"]

# L口径: name non-empty and not starting with 'sub_'
# S口径: name non-empty, not 'sub_XXXXXXXX', not 'Class::sub_XXXXXXXX'
sub_pat   = re.compile(r"^sub_[0-9A-Fa-f]{8}$")
csub_pat  = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*::sub_[0-9A-Fa-f]{8}$")
def is_L_named(name):
    n = (name or "").strip()
    return bool(n) and not n.startswith("sub_")
def is_S_named(name):
    n = (name or "").strip()
    if not n: return False
    if sub_pat.match(n) or csub_pat.match(n): return False
    if n.startswith("sub_"): return False
    # Class::sub_ also excluded
    if "::sub_" in n: return False
    return True

n = len(s15)
l_named = sum(1 for r in s15 if is_L_named(r["name"]))
s_named = sum(1 for r in s15 if is_S_named(r["name"]))
proved  = sum(1 for r in s15 if r["grade"].strip() == "[已证]")
static  = sum(1 for r in s15 if r["grade"].strip() == "[静态推断]")
unknown = sum(1 for r in s15 if r["grade"].strip() == "[未证]")
in_atlas = sum(1 for r in s15 if norm(r["entry"]) in atl_by)

# breakdown of L-named but S-unnamed (Class::sub_ placeholders)
csub_placeholder = [r for r in s15 if is_L_named(r["name"]) and not is_S_named(r["name"])]
sub_placeholder  = [r for r in s15 if (r["name"] or "").strip().startswith("sub_")]

print(f"S15 rows in coverage.tsv = {n}")
print(f"in function_atlas.tsv    = {in_atlas}")
print(f"grade [已证]={proved}  [静态推断]={static}  [未证]={unknown}")
print(f"named L口径 = {l_named}/{n} = {100*l_named/n:.2f}%")
print(f"named S口径 = {s_named}/{n} = {100*s_named/n:.2f}%")
print(f"L-named but S-unnamed (Class::sub_ placeholders) = {len(csub_placeholder)}")
print(f"plain sub_ placeholders = {len(sub_placeholder)}")
print()
print("=== Class::sub_ placeholders (counts against S but not L) ===")
for r in csub_placeholder:
    print(f"  {norm(r['entry'])}  {r['name']:<40} {r['grade']}")
print()
print("=== grade distribution by name class ===")
from collections import Counter
c = Counter()
for r in s15:
    nm = (r["name"] or "").strip()
    if sub_pat.match(nm): k="sub_XXXXXXXX"
    elif "::sub_" in nm: k="Class::sub_"
    elif not nm: k="empty"
    elif "::" in nm: k="Class::Named"
    else: k="bare Named"
    c[(k, r["grade"].strip())]+=1
for k in sorted(c): print(f"  {k}: {c[k]}")

# Dump full S15 rows to EVIDENCE
with open(os.path.join(CARD, "EVIDENCE", "T1_S15_coverage_dump.tsv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["entry","name","one_line_semantics","grade","evidence_path","in_atlas","atlas_size","L_named","S_named"])
    for r in sorted(s15, key=lambda x: norm(x["entry"])):
        e = norm(r["entry"])
        a = atl_by.get(e)
        w.writerow([e, r["name"], r["one_line_semantics"], r["grade"], r["evidence_path"],
                    "Y" if a else "N", a["size"] if a else "",
                    "1" if is_L_named(r["name"]) else "0", "1" if is_S_named(r["name"]) else "0"])
print("\nWrote EVIDENCE/T1_S15_coverage_dump.tsv")
