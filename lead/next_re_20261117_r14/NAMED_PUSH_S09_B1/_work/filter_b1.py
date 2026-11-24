# -*- coding: utf-8 -*-
"""S09 B1 筛选：subsystem==S09 and p3b2_named=='True'，排除 fn_/sub_ 地址式伪名，entry 升序取 [0:18]。"""
import csv, json, os, re
P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
WORK = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(WORK, "b1_rows.json")
PSEUDO = re.compile(r"^(fn_|sub_)[0-9A-Fa-f]{8}$")
rows = []
with open(P, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        rows.append(r)
sel_all = [r for r in rows if r["subsystem"] == "S09" and r["p3b2_named"] == "True"]
n_pseudo = sum(1 for r in sel_all if PSEUDO.match(r["name"].strip()))
sel = [r for r in sel_all if not PSEUDO.match(r["name"].strip())]
sel.sort(key=lambda r: int(r["entry"], 16))
print("S09 named=True total:", len(sel_all), " pseudo(fn_/sub_):", n_pseudo, " eligible:", len(sel))
b1 = sel[0:18]
for i, r in enumerate(b1, 1):
    print("%2d %s %-42s %-14s size=%-5s call=%-3s site=%-3s valid=%s" % (
        i, r["entry"], r["name"], r["grade"], r["size"], r["n_call"], r["n_site"], r["n_valid"]))
json.dump(b1, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("count:", len(b1))
print("-> ", OUT)
