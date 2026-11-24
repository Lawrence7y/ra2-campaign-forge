# -*- coding: utf-8 -*-
"""M59 pre-change verification: cross-check on-disk values against card claims."""
import csv, os, re, collections, sys, hashlib

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUT  = os.path.join(ROOT, "_cards", "M59-MERGE", "PRECHECK.txt")

PASS = ["006E3DB0","006E4660","006E5730","006E6080","006E6410","00727240","006CE800"]
FAIL = ["006E3E30","006E56E0","006E57A0","007276A0"]

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

lines = []
def p(s=""):
    lines.append(str(s))

atlas = set()
with open(ATLAS, encoding="utf-8-sig") as f:
    for i, line in enumerate(f):
        if i == 0: continue
        parts = line.rstrip("\r\n").split("\t")
        if parts and parts[0].strip():
            atlas.add(ne(parts[0]))

with open(COV, encoding="utf-8-sig", newline="") as f:
    cov = list(csv.reader(f, delimiter="\t"))[1:]

cov = [r for r in cov if len(r) >= 8]

# full-table grade histogram
grade_hist = collections.Counter(r[4].strip() for r in cov)
p("coverage 数据行 = %d" % len(cov))
p("全表 grade 直方图: " + repr(dict(grade_hist)))

full_zheng = sum(1 for r in cov if r[4].strip() == "[已证]")
atlas_in_zheng = sum(1 for r in cov if r[4].strip() == "[已证]" and ne(r[0]) in atlas)
atlas_out_zheng = full_zheng - atlas_in_zheng
p("全表 [已证] = %d" % full_zheng)
p("atlas 内 [已证] = %d" % atlas_in_zheng)
p("atlas 外 [已证] = %d" % atlas_out_zheng)

# per-subsystem atlas-in proved_n and proved_strict_n (strict_panel methodology)
d = collections.defaultdict(collections.Counter)
for r in cov:
    e = ne(r[0]); s = r[1].strip()
    if e not in atlas: continue
    sem = r[3]; grade = r[4].strip()
    if grade == "[已证]":
        d[s]["proved_n"] += 1
        if "[未证]" not in sem:
            d[s]["proved_strict_n"] += 1

for s in ("S15","S16"):
    p("%s atlas内 proved_n=%d proved_strict_n=%d" % (s, d[s]["proved_n"], d[s]["proved_strict_n"]))

# atlas membership + current columns for the 11 relevant rows
by_entry = {}
for r in cov:
    by_entry.setdefault(ne(r[0]), []).append(r)

p("")
p("=== 7 PASS 行现状 (entry, atlas?,  subsystem, name, col4, col5, col6, col7, col8) ===")
for e in PASS:
    rows = by_entry.get(e, [])
    p("entry=%s  count=%d  in_atlas=%s" % (e, len(rows), e in atlas))
    for r in rows:
        p("   subsystem=%s | name=%s" % (r[1], r[2]))
        p("   col4=%s" % r[3])
        p("   col5(grade)=%s" % r[4])
        p("   col6(evidence)=%s" % r[5])
        p("   col7=%s col8=%s" % (r[6], r[7]))

p("")
p("=== 4 FAIL 行现状 (grade 应不变) ===")
for e in FAIL:
    rows = by_entry.get(e, [])
    p("entry=%s  count=%d  in_atlas=%s" % (e, len(rows), e in atlas))
    for r in rows:
        p("   grade=%s evidence=%s col4=%s" % (r[4], r[5], r[3][:60]))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("WROTE", OUT)
