# -*- coding: utf-8 -*-
"""MEASURE-F3A step 1: enumerate the F3a row domain.
Domain: coverage.tsv rows where grade==[已证] AND one_line_semantics contains literal [未证]
        AND subsystem != S22.
Read-only. Writes only under MEASURE_F3A\work\.
"""
import csv, json, collections, os, io, sys

ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
OUT = os.path.join(ROOT, r"lead\next_re_20261117_r14\MEASURE_F3A\work")

COLS = ["entry", "subsystem", "name", "one_line_semantics",
        "grade", "evidence_path", "n_sources", "conflict"]

def load_cov():
    """Header line is COMMA-joined; every data line is TAB-joined (measured)."""
    out = []
    with open(COV, encoding="utf-8-sig", newline="") as f:
        for i, line in enumerate(f):
            line = line.rstrip("\r\n")
            if not line:
                continue
            parts = line.split("\t")
            if i == 0:
                assert parts[0].split(",") == COLS, parts[0]
                continue
            if len(parts) != len(COLS):
                raise SystemExit("bad field count line %d: %d" % (i + 1, len(parts)))
            out.append(dict(zip(COLS, parts)))
    return out

rows = load_cov()
print("coverage rows:", len(rows))
print("columns:", list(rows[0].keys()))

grades = collections.Counter(r["grade"] for r in rows)
print("grade distribution:", dict(grades))

# sanity: any row where semantics contains [未证] but grade not 已证?
sem_unproven = [r for r in rows if "[未证]" in (r["one_line_semantics"] or "")]
print("rows with literal [未证] in semantics (all grades):", len(sem_unproven))
print("  of those, grade breakdown:", dict(collections.Counter(r["grade"] for r in sem_unproven)))

f3a_all = [r for r in sem_unproven if r["grade"] == "[已证]"]
print("grade=[已证] AND semantics has [未证]:", len(f3a_all))
by_sub = collections.Counter(r["subsystem"] for r in f3a_all)
print("by subsystem:", dict(sorted(by_sub.items())))

f3a = [r for r in f3a_all if r["subsystem"] != "S22"]
print("non-S22:", len(f3a))
by_sub2 = collections.Counter(r["subsystem"] for r in f3a)
print("non-S22 by subsystem:", dict(sorted(by_sub2.items(), key=lambda kv: (-kv[1], kv[0]))))
print("sum check:", sum(by_sub2.values()))

# duplicates of entry inside domain?
ent = collections.Counter(r["entry"] for r in f3a)
dups = {k: v for k, v in ent.items() if v > 1}
print("duplicate entries inside domain:", dups)

json.dump({"total_rows": len(rows),
           "grade_dist": dict(grades),
           "sem_unproven_all_grades": len(sem_unproven),
           "f3a_all": len(f3a_all),
           "f3a_all_by_sub": dict(sorted(by_sub.items())),
           "f3a_nonS22": len(f3a),
           "f3a_nonS22_by_sub": dict(sorted(by_sub2.items()))},
          open(os.path.join(OUT, "s1_counts.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("OK")
