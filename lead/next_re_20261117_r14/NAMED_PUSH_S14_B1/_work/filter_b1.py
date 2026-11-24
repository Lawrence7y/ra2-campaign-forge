# -*- coding: utf-8 -*-
"""S14 B1 筛选：subsystem==S14 and p3b2_named=='True'，entry 升序前 18 行。"""
import csv, json, os
P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S14_B1\_work\b1_rows.json"
rows = []
with open(P, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        rows.append(r)
sel = [r for r in rows if r["subsystem"] == "S14" and r["p3b2_named"] == "True"]
sel.sort(key=lambda r: int(r["entry"], 16))
b1 = sel[:18]
print("S14 named=True total:", len(sel))
for i, r in enumerate(b1, 1):
    print("%2d %s %-28s %s size=%s call=%s site=%s valid=%s" % (
        i, r["entry"], r["name"], r["grade"], r["size"], r["n_call"], r["n_site"], r["n_valid"]))
json.dump(b1, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("-> ", OUT)
