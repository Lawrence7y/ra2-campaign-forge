# -*- coding: utf-8 -*-
"""S14 B2 筛选：subsystem==S14 and p3b2_named=='True'，entry 升序取 [18:36]（第 19..36 个）。"""
import csv, json, os
P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
WORK = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S14_B2\_work"
OUT = os.path.join(WORK, "b2_rows.json")
rows = []
with open(P, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        rows.append(r)
sel = [r for r in rows if r["subsystem"] == "S14" and r["p3b2_named"] == "True"]
sel.sort(key=lambda r: int(r["entry"], 16))
print("S14 named=True total:", len(sel))
b2 = sel[18:36]
for i, r in enumerate(b2, 19):
    print("%2d %s %-30s %-14s size=%-5s call=%-3s site=%-3s valid=%s" % (
        i, r["entry"], r["name"], r["grade"], r["size"], r["n_call"], r["n_site"], r["n_valid"]))
json.dump(b2, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("count:", len(b2))
print("-> ", OUT)
