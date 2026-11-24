# -*- coding: utf-8 -*-
"""筛选 S01+S03 named 候选（排除 fn_/sub_ 伪名，按 entry 升序），落盘本批清单。"""
import csv, re, os
BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
SRC = os.path.join(BASE, r"SURVEY_3B2\hits_detail.tsv")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rows.tsv")
rows = [r for r in csv.DictReader(open(SRC, encoding="utf-8"), delimiter="\t")
        if r["subsystem"] in ("S01", "S03") and r["p3b2_named"] == "True"]
pseudo = re.compile(r"^(fn|sub)_[0-9A-Fa-f]{8}$")
excluded = [r for r in rows if pseudo.match(r["name"])]
rows = [r for r in rows if not pseudo.match(r["name"])]
rows.sort(key=lambda r: int(r["entry"], 16))
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["entry", "subsystem", "name", "grade", "size", "n_call", "n_site"])
    for r in rows:
        w.writerow([r["entry"], r["subsystem"], r["name"], r["grade"], r["size"], r["n_call"], r["n_site"]])
print("named(raw)=", 5 + len(excluded), " excluded_pseudo=", len(excluded), " kept=", len(rows))
for i, r in enumerate(rows, 1):
    print(i, r["entry"], r["subsystem"], r["name"], "size=", r["size"], "ncall=", r["n_call"], "nsite=", r["n_site"])
