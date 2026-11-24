# -*- coding: utf-8 -*-
"""NAMED-PUSH S22 B4: print the full candidate filter + slice accounting (for REPORT)."""
import csv, re

HITS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
FN = re.compile(r"^fn_[0-9A-Fa-f]{8}$")
SUB = re.compile(r"^sub_[0-9A-Fa-f]{8}$")

with open(HITS, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f, delimiter="\t"))
named = [r for r in rows if r["subsystem"] == "S22" and r["p3b2_named"] == "True"]
pseudo = [r for r in named if FN.match(r["name"]) or SUB.match(r["name"])]
filtered = [r for r in named if not (FN.match(r["name"]) or SUB.match(r["name"]))]
filtered.sort(key=lambda r: int(r["entry"], 16))
print("S22 named=True rows:", len(named))
print("pseudo (fn_/sub_) rows among named:", len(pseudo))
print("after pseudo-exclusion:", len(filtered))
print("B1 [0:18]:", 18, filtered[0]["entry"], "..", filtered[17]["entry"])
print("B2 [18:36]:", 18, filtered[18]["entry"], "..", filtered[35]["entry"])
print("B3 [36:49]:", 13, filtered[36]["entry"], "..", filtered[48]["entry"])
print("B4 [49:] remaining:", len(filtered) - 49, filtered[49]["entry"], "..", filtered[-1]["entry"])
print("---- B4 factory-family (first 13) ----")
for r in filtered[49:62]:
    print(r["entry"], r["name"])
print("---- B4 vector-family (remaining 9) ----")
for r in filtered[62:]:
    print(r["entry"], r["name"])
