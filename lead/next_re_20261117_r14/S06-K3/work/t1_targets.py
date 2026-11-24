#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T1: build S06 TARGETS.tsv and recompute S06 panel numbers from disk.
Reads coverage.tsv (subsystem==S06) intersect function_atlas.tsv.
Named caliber R14-R14: L = name nonempty & not startswith 'sub_';
S = L and not containing 'Class::sub_'. proved = grade '[已证]'.
"""
import os, math
from collections import Counter

ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
CARD = os.path.join(ROOT, r"lead\next_re_20261117_r14\S06-K3")
OUT_TSV = os.path.join(CARD, "TARGETS.tsv")
OUT_TXT = os.path.join(CARD, "EVIDENCE", "t1_stats.txt")


def read_tsv(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    hdr = lines[0].split("\t")
    rows = []
    for ln in lines[1:]:
        if not ln.strip():
            continue
        parts = ln.split("\t")
        if len(parts) < len(hdr):
            parts += [""] * (len(hdr) - len(parts))
        rows.append(dict(zip(hdr, parts)))
    return hdr, rows


_, atlas_rows = read_tsv(ATLAS)
_, cov_rows = read_tsv(COV)

atlas = {r["entry"].upper(): r for r in atlas_rows}

cov_all_entries = [r["entry"].upper() for r in cov_rows]
dups = {e: c for e, c in Counter(cov_all_entries).items() if c > 1}

s06_all = [r for r in cov_rows if r["subsystem"] == "S06"]
s06_atlas = [r for r in s06_all if r["entry"].upper() in atlas]


def is_named_L(name):
    return bool(name) and not name.startswith("sub_")


def is_class_sub(name):
    return "Class::sub_" in name


def is_named_S(name):
    return is_named_L(name) and not is_class_sub(name)


named_L = sum(1 for r in s06_atlas if is_named_L(r["name"]))
named_S = sum(1 for r in s06_atlas if is_named_S(r["name"]))
class_sub = sum(1 for r in s06_atlas if is_class_sub(r["name"]))
proved = sum(1 for r in s06_atlas if r["grade"] == "[已证]")
static_inf = sum(1 for r in s06_atlas if r["grade"] == "[静态推断]")
unproven = sum(1 for r in s06_atlas if r["grade"] == "[未证]")
atlas_n = len(s06_atlas)
s06_in_cov_total = len(s06_all)

gate50 = math.ceil(0.5 * atlas_n)
gap50 = gate50 - proved

# any nonstandard grade tokens in S06?
grade_tokens = Counter(r["grade"] for r in s06_atlas)

# TARGETS.tsv: entry, size, n_instr, n_callers, n_callees, name, grade,
# one_line_semantics, named_L, named_S, evidence_path
thdr = ["entry", "size", "n_instr", "n_callers", "n_callees", "name", "grade",
        "one_line_semantics", "named_L", "named_S", "evidence_path"]
lines = ["\t".join(thdr)]
for r in sorted(s06_atlas, key=lambda x: x["entry"].upper()):
    e = r["entry"].upper()
    a = atlas[e]
    nl = "1" if is_named_L(r["name"]) else "0"
    ns = "1" if is_named_S(r["name"]) else "0"
    sem = r["one_line_semantics"].replace("\t", " ").replace("\n", " ")
    nm = r["name"].replace("\t", " ").replace("\n", " ")
    ev = r["evidence_path"].replace("\t", " ").replace("\n", " ")
    lines.append("\t".join([e, a["size"], a["n_instr"], a["n_callers"],
                            a["n_callees"], nm, r["grade"], sem, nl, ns, ev]))
with open(OUT_TSV, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines) + "\n")

report = []
report.append("=== T1 S06 recompute from disk ===")
report.append(f"coverage.tsv data rows      = {len(cov_rows)}")
report.append(f"function_atlas.tsv rows     = {len(atlas_rows)}")
report.append(f"coverage duplicate entries  = {len(dups)}")
report.append(f"S06 rows in coverage(total) = {s06_in_cov_total}")
report.append(f"S06 intersect atlas (atlas_n)= {atlas_n}")
report.append(f"named_L = {named_L}  ({named_L/atlas_n*100:.2f}%)")
report.append(f"Class::sub_ (in L) = {class_sub}")
report.append(f"named_S = {named_S}  ({named_S/atlas_n*100:.2f}%)")
report.append(f"proved ([已证]) = {proved}  ({proved/atlas_n*100:.2f}%)")
report.append(f"[静态推断] = {static_inf}  [未证] = {unproven}")
report.append(f"grade tokens = {dict(grade_tokens)}")
report.append(f"50% gate (ceil(0.5*{atlas_n})) = {gate50}")
report.append(f"gap to 50% = {gate50} - {proved} = {gap50}")
report.append("")
report.append("--- cross-check vs dispatch-card numbers (STALE, do NOT use) ---")
report.append("card: atlas 850 / named 385 (45.29%) / proved 96 (11.29%)")
report.append(f"disk: atlas {atlas_n} / named_L {named_L} / named_S {named_S} / proved {proved}")
report.append("PANEL.md on disk (line 38): atlas_n=848 named_n=384 L=45.28 S=45.17 proved_n=103 (12.15)")
report.append("=> card numbers disagree with PANEL.md on disk; use disk values (discipline 9).")
report.append("")
report.append("--- named_S Class::sub_ entries in S06 ---")
for r in s06_atlas:
    if is_class_sub(r["name"]):
        report.append(f"  {r['entry'].upper()}  {r['name']}  grade={r['grade']}")
with open(OUT_TXT, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(report) + "\n")

print("\n".join(report))
print(f"\nWrote {OUT_TSV} ({len(lines)-1} data rows)")
