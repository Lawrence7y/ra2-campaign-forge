#!/usr/bin/env python3
"""T1: Filter coverage.tsv for subsystem==S17, compute denominators/grouping.
Read-only on all inputs. Writes only into S17-K2\ work dir.
"""
import csv, re, sys, os

ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
OUTDIR = os.path.join(ROOT, r"lead\next_re_20261117_r14\S17-K2")

def is_named(name):
    n = (name or "").strip()
    if not n: return False
    # sub_XXXXXXXX (8 hex) or sub_XXXXXXXX_... are anonymous
    if re.fullmatch(r"sub_[0-9A-Fa-f]{8}(?:_\d+)?", n): return False
    if n.lower().startswith("sub_") and re.fullmatch(r"sub_[0-9a-fA-F]{8}.*", n): return False
    return True

# load atlas entries
atlas = set()
with open(ATLAS, "r", encoding="utf-8", errors="replace") as f:
    r = csv.DictReader(f, delimiter="\t")
    for row in r:
        e = (row["entry"] or "").strip().upper()
        if e: atlas.add(e)

# load coverage
s17 = []
total = 0
grade_all = {}
with open(COV, "r", encoding="utf-8", errors="replace") as f:
    r = csv.DictReader(f, delimiter="\t")
    for row in r:
        total += 1
        g = (row.get("grade") or "").strip()
        grade_all[g] = grade_all.get(g,0)+1
        if (row.get("subsystem") or "").strip().upper() == "S17":
            e = (row.get("entry") or "").strip().upper()
            s17.append({
                "entry": e,
                "name": (row.get("name") or "").strip(),
                "grade": g,
                "sem": (row.get("one_line_semantics") or "").strip(),
                "ev": (row.get("evidence_path") or "").strip(),
                "nsrc": (row.get("n_sources") or "").strip(),
                "conflict": (row.get("conflict") or "").strip(),
                "in_atlas": e in atlas,
            })

# group
atlas_rows = [r for r in s17 if r["in_atlas"]]
outside_rows = [r for r in s17 if not r["in_atlas"]]

def stats(rows, label):
    n = len(rows)
    named = sum(1 for r in rows if is_named(r["name"]))
    proved = sum(1 for r in rows if r["grade"] == "[已证]")
    static = sum(1 for r in rows if r["grade"] == "[静态推断]")
    unprov = sum(1 for r in rows if r["grade"] == "[未证]")
    named_proved = sum(1 for r in rows if is_named(r["name"]) and r["grade"]=="[已证]")
    print(f"{label}: n={n} named={named} ({100*named/n if n else 0:.2f}%) proved={proved} ({100*proved/n if n else 0:.2f}%) static={static} unprov={unprov} named&proved={named_proved}")

print(f"coverage total data rows = {total}")
print(f"coverage grade distribution (all) = {grade_all}")
print(f"S17 total rows (all coverage) = {len(s17)}")
print(f"S17 atlas-internal rows = {len(atlas_rows)}")
print(f"S17 outside-atlas rows = {len(outside_rows)}")
stats(atlas_rows, "ATLAS-INTERNAL")
stats(s17, "FULL-COVERAGE")
print()
print("grade breakdown atlas-internal:")
gb = {}
for r in atlas_rows: gb[r["grade"]] = gb.get(r["grade"],0)+1
print(gb)
print("grade breakdown full-coverage:")
gb2 = {}
for r in s17: gb2[r["grade"]] = gb2.get(r["grade"],0)+1
print(gb2)

# Write TARGETS.tsv (all S17 rows, atlas first)
out = os.path.join(OUTDIR, "TARGETS.tsv")
with open(out, "w", encoding="utf-8", errors="replace", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["entry","in_atlas","current_name","current_grade","current_semantics","named?","缺什么","我打算怎么取证"])
    for r in sorted(atlas_rows, key=lambda x:x["entry"]) + sorted(outside_rows, key=lambda x:x["entry"]):
        nm = is_named(r["name"])
        gap = []
        if not nm: gap.append("name")
        if r["grade"] != "[已证]": gap.append("proof:"+r["grade"])
        if not r["sem"] or r["sem"].startswith("[未证]"): gap.append("semantics")
        w.writerow([r["entry"], "Y" if r["in_atlas"] else "N", r["name"], r["grade"], r["sem"],
                    "Y" if nm else "N", ";".join(gap) if gap else "OK", ""])

# machine-readable dump for later scripts
import json
with open(os.path.join(OUTDIR,"work","s17_rows.json"),"w",encoding="utf-8") as f:
    json.dump(s17, f, ensure_ascii=False, indent=1)

print(f"\nWrote {out}")
