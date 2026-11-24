# -*- coding: utf-8 -*-
"""S22 B5 筛选：subsystem==S22 & p3b2_named==True, 排除 fn_/sub_ 伪名, 升序最后 9 行 [62:71]。"""
import csv, json, os

BASE = r"D:\Project\ra2-campaign-forge"
SURVEY = os.path.join(BASE, r"lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv")

rows = []
with open(SURVEY, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if (r.get("subsystem") == "S22" and r.get("p3b2_named") == "True"
                and not r["name"].startswith("fn_") and not r["name"].startswith("sub_")):
            rows.append(r)
rows.sort(key=lambda r: int(r["entry"], 16))

sel = rows[62:71]
print("S22 named (no pseudo) =", len(rows), " | B5 slice [62:71] =", len(sel))
for r in sel:
    print(r["entry"], r["name"], "size=" + r["size"], "ncall=" + r["n_call"], "nsite=" + r["n_site"])

with open(os.path.join(os.path.dirname(__file__), "b5_rows.json"), "w", encoding="utf-8") as f:
    json.dump(sel, f, ensure_ascii=False, indent=1)
