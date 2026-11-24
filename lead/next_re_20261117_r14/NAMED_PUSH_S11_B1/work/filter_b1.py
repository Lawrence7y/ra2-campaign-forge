# -*- coding: utf-8 -*-
"""S11 B1 候选筛选：subsystem==S11 且 p3b2_named==True，排除 fn_/sub_ 伪名，按 entry 升序取前 18。"""
import csv, json, os, sys

SURVEY = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S11_B1\work\b1_rows.json"

rows = list(csv.DictReader(open(SURVEY, encoding="utf-8"), delimiter="\t"))
s11 = [r for r in rows if r["subsystem"] == "S11"]
named = [r for r in s11 if r["p3b2_named"] == "True"]

def is_pseudo(n):
    b = n.split("::")[-1]
    return b.startswith("fn_") or b.startswith("sub_") or n.startswith("fn_") or n.startswith("sub_")

pseudo = [r for r in named if is_pseudo(r["name"])]
real = [r for r in named if not is_pseudo(r["name"])]
real.sort(key=lambda r: int(r["entry"], 16))
batch = real[:18]

print("S11 hits total          :", len(s11))
print("S11 p3b2_named==True    :", len(named))
print("  其中 fn_/sub_ 伪名    :", len(pseudo), [r["name"] for r in pseudo])
print("  真名/slotN 可用       :", len(real))
print("本批取前 18             :", len(batch))
for i, r in enumerate(batch, 1):
    print(f"  {i:2d} {r['entry']}  {r['name']}")

json.dump(batch, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("written:", OUT)
