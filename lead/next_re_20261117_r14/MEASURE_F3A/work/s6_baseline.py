# -*- coding: utf-8 -*-
"""MEASURE-F3A step 3: baseline proved / denominators per subsystem, reproduced
independently so the "after downgrade" numbers rest on the same base.

口径 (same as M4_merge\_audit\a1_core.py, quoted by AUDIT-MARGIN):
  denominator n = |coverage rows with that subsystem  ∩  W130 function_atlas entries|
  proved        = rows with grade == [已证]
  thresholds    = named ceil(0.9n), proved ceil(0.5n)
  S22 excluded from ranking entirely.
"""
import csv, json, os, sys, collections, math

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
OUT = os.path.join(ROOT, r"lead\next_re_20261117_r14\MEASURE_F3A\work")
COLS = ["entry", "subsystem", "name", "one_line_semantics",
        "grade", "evidence_path", "n_sources", "conflict"]

def load_cov():
    out = []
    with open(COV, encoding="utf-8-sig", newline="") as f:
        for i, line in enumerate(f):
            line = line.rstrip("\r\n")
            if not line:
                continue
            p = line.split("\t")
            if i == 0:
                continue
            out.append(dict(zip(COLS, p)))
    return out

rows = load_cov()
atlas = {}
with open(ATLAS, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        atlas[r["entry"].upper()] = r

def named_S(r):
    nm = (r["name"] or "").strip()
    if not nm or nm.startswith("sub_"):
        return False
    if "::sub_" in nm:
        return False
    return True

def named_L(r):
    nm = (r["name"] or "").strip()
    return bool(nm) and not nm.startswith("sub_")

subs = sorted({r["subsystem"] for r in rows if r["subsystem"] != "S22"})
res = {}
for s in subs:
    all_rows = [r for r in rows if r["subsystem"] == s]
    in_atlas = [r for r in all_rows if r["entry"].upper() in atlas]
    n = len(in_atlas)
    proved = sum(1 for r in in_atlas if r["grade"] == "[已证]")
    res[s] = {"n": n, "n_cov": len(all_rows),
              "named_L": sum(1 for r in in_atlas if named_L(r)),
              "named_S": sum(1 for r in in_atlas if named_S(r)),
              "proved": proved,
              "thr_named": math.ceil(0.9 * n), "thr_proved": math.ceil(0.5 * n)}

print("%-5s %6s %6s %7s %7s %6s %6s %6s  %s" %
      ("sub", "n", "nCov", "named_S", "proved", "thN", "thP", "pctP", "达标"))
tot = 0
for s in subs:
    d = res[s]
    pct = 100.0 * d["proved"] / d["n"] if d["n"] else 0
    ok = (d["named_S"] >= d["thr_named"]) and (d["proved"] >= d["thr_proved"])
    tot += 1 if ok else 0
    print("%-5s %6d %6d %7d %7d %6d %6d %6.1f  %s" %
          (s, d["n"], d["n_cov"], d["named_S"], d["proved"], d["thr_named"],
           d["thr_proved"], pct, "OK" if ok else "-"))
print("subsystems:", len(subs), " 达标:", tot)
print()
for s in ("S15", "S16", "S17"):
    d = res[s]
    print("%s: n=%d named_S=%d proved=%d thrN=%d thrP=%d  ->  named %d/%d  proved %d/%d"
          % (s, d["n"], d["named_S"], d["proved"], d["thr_named"], d["thr_proved"],
             d["named_S"], d["n"], d["proved"], d["n"]))

json.dump(res, open(os.path.join(OUT, "s6_baseline.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
