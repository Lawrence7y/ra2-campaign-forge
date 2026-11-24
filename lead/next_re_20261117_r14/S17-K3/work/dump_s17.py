#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump all S17 coverage rows (current names/grades) for target selection."""
import csv, io, os, sys
ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
with io.open(COV, "r", encoding="utf-8-sig", newline="") as f:
    cov = list(csv.DictReader(f, delimiter="\t"))
with io.open(ATLAS, "r", encoding="utf-8-sig", newline="") as f:
    atlas = list(csv.DictReader(f, delimiter="\t"))
asize = {r["entry"].lower(): r["size"] for r in atlas}
aent = set(asize)

s17 = [r for r in cov if r.get("subsystem") == "S17"]
out = []
out.append("=== ALL S17 rows (name/grade), atlas marked ===")
out.append("entry\tsize\tinAtlas\tname\tgrade\tsem")
for r in sorted(s17, key=lambda x: x["entry"]):
    e = r["entry"].lower()
    out.append("\t".join([r["entry"], asize.get(e,"-"), "Y" if e in aent else "N",
                          r.get("name",""), r.get("grade",""), r.get("one_line_semantics","")]))
# K2 delta entries status
k2 = ["0041D6E0","0043A5D0","004B6BB0","0067C690","0055AAC0","00539AE0","00431B80"]
by = {r["entry"].upper(): r for r in cov}
out.append("")
out.append("=== K2 delta entries current status ===")
for e in k2:
    r = by.get(e.upper())
    if r: out.append(f"{e}\tname={r['name']}\tgrade={r['grade']}\tsem={r['one_line_semantics']}")
    else: out.append(f"{e}\tNOT FOUND")

txt = "\n".join(out) + "\n"
CARD = os.path.join(ROOT, r"lead\next_re_20261117_r14\S17-K3")
with io.open(os.path.join(CARD,"EVIDENCE","s17_name_landscape.txt"),"w",encoding="utf-8") as f:
    f.write(txt)
sys.stdout.write("written\n")
