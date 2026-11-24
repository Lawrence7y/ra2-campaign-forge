# -*- coding: utf-8 -*-
"""Generate b3_rows.json (my 13 candidate rows) from hits_detail.tsv, same filter as filter_b3.py."""
import csv, os, re, json

HITS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
HERE = os.path.dirname(os.path.abspath(__file__))
FN = re.compile(r"^fn_[0-9A-Fa-f]{8}$")
SUB = re.compile(r"^sub_[0-9A-Fa-f]{8}$")

with open(HITS, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f, delimiter="\t"))
named = [r for r in rows if r["subsystem"] == "S22" and r["p3b2_named"] == "True"]
filtered = [r for r in named if not (FN.match(r["name"]) or SUB.match(r["name"]))]
filtered.sort(key=lambda r: int(r["entry"], 16))
b3 = filtered[36:49]
for r in b3:
    r["entry"] = r["entry"].strip().upper()
    r["name"] = r["name"].strip()
    for k in ("size", "n_insn", "n_call", "n_site", "n_valid"):
        r[k] = int(r[k])
with open(os.path.join(HERE, "b3_rows.json"), "w", encoding="utf-8") as f:
    json.dump({"rows": b3}, f, ensure_ascii=False, indent=1)
print("wrote", len(b3), "rows")
for r in b3:
    print(r["entry"], r["name"], r["size"])
