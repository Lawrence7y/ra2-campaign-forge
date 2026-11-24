#!/usr/bin/env python3
# S18-K2 T1: build TARGETS.tsv and compute S18 named/proved statistics from disk.
# R14-R14 named: L = name nonempty and not starting with 'sub_'
#                S = L and not 'Class::sub_' form
import csv, os, sys

COV  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATL  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
OUTD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S18-K2"

def norm(e):
    return e.strip().upper()

# --- atlas set (entry -> row) ---
atlas = {}
with open(ATL, "r", encoding="utf-8", newline="") as f:
    r = csv.DictReader(f, delimiter="\t")
    for row in r:
        e = norm(row["entry"])
        if e:
            atlas[e] = row
print("atlas data rows:", len(atlas))

# --- coverage rows ---
cov = []
with open(COV, "r", encoding="utf-8", newline="") as f:
    r = csv.DictReader(f, delimiter="\t")
    for row in r:
        cov.append(row)
print("coverage data rows:", len(cov))

# --- S18 rows ∩ atlas ---
s18 = [row for row in cov if row["subsystem"].strip() == "S18"]
s18_atlas = [row for row in s18 if norm(row["entry"]) in atlas]
print("S18 total rows in coverage:", len(s18))
print("S18 rows ∩ atlas (atlas_n):", len(s18_atlas))

def is_named_L(name):
    n = (name or "").strip()
    return len(n) > 0 and not n.lower().startswith("sub_")

def is_named_S(name):
    n = (name or "").strip()
    if not is_named_L(n):
        return False
    # exclude Class::sub_XXXXXXXX (R14-R14 S caliber)
    low = n.lower()
    if "::sub_" in low:
        return False
    return True

namedL = sum(1 for row in s18_atlas if is_named_L(row["name"]))
namedS = sum(1 for row in s18_atlas if is_named_S(row["name"]))
proved = sum(1 for row in s18_atlas if row["grade"].strip() == "[已证]")
grade_dist = {}
for row in s18_atlas:
    g = row["grade"].strip()
    grade_dist[g] = grade_dist.get(g, 0) + 1
print("S18 atlas named_L:", namedL, " pct=%.2f%%" % (100.0*namedL/len(s18_atlas)))
print("S18 atlas named_S:", namedS, " pct=%.2f%%" % (100.0*namedS/len(s18_atlas)))
print("S18 atlas proved:", proved, " pct=%.2f%%" % (100.0*proved/len(s18_atlas)))
print("S18 atlas grade dist:", grade_dist)

# also full-table S18 (not just atlas) for reference
namedL_all = sum(1 for row in s18 if is_named_L(row["name"]))
proved_all = sum(1 for row in s18 if row["grade"].strip() == "[已证]")
print("S18 ALL rows named_L:", namedL_all, "proved:", proved_all, "of", len(s18))

# 50% threshold
for den_label, den in [("atlas_n", len(s18_atlas)), ("card_660", 660), ("PANEL_659", 659)]:
    target = den // 2 if den % 2 == 0 else den // 2 + 1  # ceil(0.5*den)
    print("threshold 50%% of %s=%d -> need %d proved, currently %d, gap=%d" %
          (den_label, den, target, proved, target-proved))

# --- TARGETS.tsv : subsystem==S18 ∩ atlas ---
# columns: entry, size, n_instr, n_callers, name, grade, one_line_semantics, evidence_path, in_atlas
tgt = os.path.join(OUTD, "TARGETS.tsv")
with open(tgt, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["entry","size","n_instr","n_callers","name","grade","one_line_semantics","evidence_path","in_atlas"])
    for row in s18_atlas:
        a = atlas[norm(row["entry"])]
        w.writerow([norm(row["entry"]), a["size"], a["n_instr"], a["n_callers"],
                    row["name"], row["grade"], row["one_line_semantics"], row["evidence_path"], "1"])
print("wrote", tgt, "rows:", len(s18_atlas))
