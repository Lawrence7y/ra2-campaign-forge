# -*- coding: utf-8 -*-
"""筛选 S12 B1 的 18 个候选。只读 hits_detail.tsv。"""
import csv, json, os, re

P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rows_b1.json")

PSEUDO = re.compile(r"(^|::)(fn|sub)_[0-9A-Fa-f]{8}$")

rows = []
with open(P, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r["subsystem"] != "S12":
            continue
        if r["p3b2_named"] != "True":
            continue
        rows.append(r)

rows.sort(key=lambda r: int(r["entry"], 16))
print("S12 p3b2_named=True: %d" % len(rows))
pseudo = [r for r in rows if PSEUDO.search(r["name"])]
print("伪名(fn_/sub_)行: %d -> %s" % (len(pseudo), [r["entry"] for r in pseudo]))
sel = [r for r in rows if not PSEUDO.search(r["name"])]
print("排除后: %d" % len(sel))
b1 = sel[:18]
for i, r in enumerate(b1, 1):
    print("%2d %s %s size=%s n_call=%s" % (i, r["entry"], r["name"], r["size"], r["n_call"]))
json.dump(b1, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("->", OUT)
