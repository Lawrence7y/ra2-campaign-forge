# -*- coding: utf-8 -*-
"""S13-PUSH Step 0: 抽取 proved 候选池
池 = coverage.tsv 中 subsystem==S13 且 grade ∈ {[静态推断],[未证]} 且 entry 在 atlas 内。
atlas entry 小写，coverage entry 大写 —— 统一归一为大写 8 位十六进制。
输出 work/pool.json（含 atlas size / n_instr / 现有 name/semantics/grade）。
"""
import csv, json, os, collections

BASE = r"D:\Project\ra2-campaign-forge"
COV  = os.path.join(BASE, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS= os.path.join(BASE, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
OUT  = os.path.join(BASE, r"lead\next_re_20261117_r14\S13_PUSH\work")

def norm(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

atlas = {}
with open(ATLAS, encoding="utf-8-sig") as f:
    rdr = csv.reader(f, delimiter="\t")
    next(rdr)
    for row in rdr:
        if not row or not row[0].strip():
            continue
        try:
            atlas[norm(row[0])] = {"size": int(row[1]), "n_instr": int(row[2]),
                                   "n_callers": int(row[3]) if len(row) > 3 else None}
        except (ValueError, IndexError):
            pass

pool = []
grade_all = collections.Counter()
with open(COV, encoding="utf-8-sig") as f:
    first = f.readline()  # comma header
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 6:
            continue
        entry = parts[0].strip(); subsystem = parts[1].strip()
        if subsystem != "S13":
            continue
        e = norm(entry)
        if e not in atlas:
            continue
        grade = parts[4].strip()
        grade_all[grade] += 1
        if grade in ("[静态推断]", "[未证]"):
            pool.append({
                "entry": e,
                "subsystem": subsystem,
                "name": parts[2].strip(),
                "semantics": parts[3].strip(),
                "grade": grade,
                "evidence_path": parts[5].strip() if len(parts) > 5 else "",
                "atlas_size": atlas[e]["size"],
                "atlas_n_instr": atlas[e]["n_instr"],
                "atlas_n_callers": atlas[e]["n_callers"],
            })

pool.sort(key=lambda p: p["entry"])
json.dump(pool, open(os.path.join(OUT, "pool.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("S13 atlas grade distribution:", dict(grade_all))
print("POOL (S13 atlas & [静态推断]/[未证]) size =", len(pool))
print("  by grade:", dict(collections.Counter(p["grade"] for p in pool)))
print("  with name != sub_*:", sum(1 for p in pool if p["name"] and not p["name"].startswith("sub_")))
