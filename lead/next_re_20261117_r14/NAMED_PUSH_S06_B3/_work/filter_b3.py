# -*- coding: utf-8 -*-
"""S06 B3 筛选：subsystem==S06 and p3b2_named=='True'，排除 fn_/sub_ 伪名，
entry 升序取第 37..54 行（0-based [36:54]）。候选不足 18 时取到末尾。"""
import csv, json, re, os
P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S06_B3\_work\b3_rows.json"
rows = []
with open(P, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        rows.append(r)

def is_pseudo(n):
    return bool(re.fullmatch(r"(fn|sub)_[0-9A-Fa-f]{8}", n))

sel_all = [r for r in rows if r["subsystem"] == "S06" and r["p3b2_named"] == "True"]
sel = [r for r in sel_all if not is_pseudo(r["name"])]
pseudo = [r for r in sel_all if is_pseudo(r["name"])]
sel.sort(key=lambda r: int(r["entry"], 16))
b3 = sel[36:54]   # 1-based #37..#54 == 0-based [36:54]
print("S06 named=True total:", len(sel_all), " pseudo excluded:", len(pseudo), " real:", len(sel))
for i, r in enumerate(sel, 1):
    mark = "*B3*" if 37 <= i <= 54 else (" B1" if i <= 18 else (" B2" if i <= 36 else "   "))
    print("%2d %s %-52s %s %s size=%s call=%s site=%s valid=%s" % (
        i, r["entry"], r["name"], r["grade"], mark, r["size"], r["n_call"], r["n_site"], r["n_valid"]))
json.dump(b3, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("-> ", OUT, " rows=", len(b3))
