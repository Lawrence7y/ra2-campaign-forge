# -*- coding: utf-8 -*-
"""
S15S16-3B2 Step 0: extract pool (coverage subsystem in {S15,S16}, grade == [静态推断])
and join with atlas (case-normalized). Emits work/pool.json with entry/subsystem/name/
semantics/grade/atlas_size/in_atlas.
"""
import csv, json, os

BASE = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(BASE, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS = os.path.join(BASE, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
OUT = os.path.join(BASE, r"lead\next_re_20261117_r14\S15S16_3B2\work")

def norm(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    return e

# atlas: entry(size lowercase hex) -> size, n_instr
atlas = {}
with open(ATLAS, encoding="utf-8") as f:
    rdr = csv.reader(f, delimiter="\t")
    header = next(rdr)
    for row in rdr:
        if not row or not row[0].strip():
            continue
        e = norm(row[0])
        try:
            size = int(row[1])
            ninstr = int(row[2])
        except (ValueError, IndexError):
            continue
        atlas[e] = {"size": size, "n_instr": ninstr}

# coverage: skip header (comma), split data by tab
pool = []
with open(COV, encoding="utf-8") as f:
    first = f.readline()  # header, comma-separated
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 5:
            continue
        entry = parts[0].strip()
        subsystem = parts[1].strip()
        name = parts[2].strip()
        semantics = parts[3].strip()
        grade = parts[4].strip()
        if subsystem in ("S15", "S16") and grade == "[静态推断]":
            e = norm(entry)
            a = atlas.get(e)
            pool.append({
                "entry": e,
                "subsystem": subsystem,
                "name": name,
                "semantics": semantics,
                "grade": grade,
                "atlas_size": a["size"] if a else None,
                "atlas_n_instr": a["n_instr"] if a else None,
                "in_atlas": a is not None,
            })

with open(os.path.join(OUT, "pool.json"), "w", encoding="utf-8") as f:
    json.dump(pool, f, ensure_ascii=False, indent=2)

from collections import Counter
print("pool size", len(pool))
for s in ("S15", "S16"):
    ps = [p for p in pool if p["subsystem"] == s]
    print(s, "pool", len(ps), "in_atlas", sum(1 for p in ps if p["in_atlas"]),
          "out_atlas", sum(1 for p in ps if not p["in_atlas"]))
