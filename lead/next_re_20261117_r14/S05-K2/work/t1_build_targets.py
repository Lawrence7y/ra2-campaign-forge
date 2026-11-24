#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S05-K2 T1: build TARGETS.tsv = (coverage S05) ∩ (function_atlas), case-normalized.
Also compute named(L/S) and proved counts per R14-R14, plus distance to 50% threshold."""
import csv, os, re, json

ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATL = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
OUTDIR = os.path.join(ROOT, r"lead\next_re_20261117_r14\S05-K2")

def norm(e):
    return e.strip().upper()

# --- read coverage S05 ---
cov_rows = []
with open(COV, encoding="utf-8") as f:
    r = csv.DictReader(f, delimiter="\t")
    for row in r:
        if row["subsystem"] == "S05":
            row["_entry"] = norm(row["entry"])
            cov_rows.append(row)

# --- read atlas (entry lowercase) into set + size map ---
atl = {}
with open(ATL, encoding="utf-8") as f:
    r = csv.DictReader(f, delimiter="\t")
    for row in r:
        atl[norm(row["entry"])] = row

cov_by_entry = {row["_entry"]: row for row in cov_rows}

# intersection
inter = sorted(set(cov_by_entry) & set(atl))

# S05 rows NOT in atlas (for info)
cov_s05_all = len(cov_rows)
cov_s05_in_atlas = len(inter)

# named口径 L: name nonempty and not starting with sub_ (case-insensitive 'sub_')
# named口径 S: L minus "Class::sub_XXXXXXXX" self-placeholder names
def is_named_L(name):
    n = (name or "").strip()
    if not n:
        return False
    if n.lower().startswith("sub_"):
        return False
    return True

def is_class_sub_placeholder(name):
    # Class::sub_XXXXXXXX 属自造占位名（hex 位数不固定，可为 6/8 位）
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*::sub_[0-9A-Fa-f]+$", (name or "").strip()))

def is_named_S(name):
    return is_named_L(name) and not is_class_sub_placeholder(name)

named_L = 0
named_S = 0
proved = 0
static_infer = 0
unproved = 0
grade_dist = {}
class_sub_list = []
for e in inter:
    row = cov_by_entry[e]
    name = row["name"]
    grade = row["grade"]
    grade_dist[grade] = grade_dist.get(grade, 0) + 1
    if is_named_L(name):
        named_L += 1
    if is_named_S(name):
        named_S += 1
    else:
        if is_class_sub_placeholder(name):
            class_sub_list.append((e, name))
    if grade == "[已证]":
        proved += 1
    elif grade == "[静态推断]":
        static_infer += 1
    else:
        unproved += 1

atlas_n = len(inter)  # denominator A for S05 (per-PANEL atlas_n)
thr50 = int(atlas_n * 0.5 + 0.999999)  # ceil(0.5*N)
short50 = max(0, thr50 - proved)

# Write TARGETS.tsv
out = os.path.join(OUTDIR, "TARGETS.tsv")
with open(out, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["entry", "atlas_size", "subsystem", "name", "grade", "one_line_semantics", "named_L", "named_S"])
    for e in inter:
        row = cov_by_entry[e]
        name = row["name"]
        w.writerow([
            e, atl[e]["size"], "S05", name, row["grade"],
            row["one_line_semantics"].replace("\t", " ").replace("\n", " "),
            "1" if is_named_L(name) else "0",
            "1" if is_named_S(name) else "0",
        ])

result = {
    "cov_s05_all_rows": cov_s05_all,
    "atlas_total": len(atl),
    "atlas_n_S05_intersection": atlas_n,
    "named_L": named_L,
    "named_S": named_S,
    "named_pct_L": round(100.0*named_L/atlas_n, 4),
    "named_pct_S": round(100.0*named_S/atlas_n, 4),
    "proved": proved,
    "proved_pct": round(100.0*proved/atlas_n, 4),
    "grade_dist": grade_dist,
    "class_sub_placeholders": class_sub_list,
    "threshold_50pct_ceil": thr50,
    "short_of_50pct": short50,
    "cov_s05_not_in_atlas": cov_s05_all - atlas_n,
}
with open(os.path.join(OUTDIR, "work", "t1_stats.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(json.dumps(result, ensure_ascii=False, indent=2))
