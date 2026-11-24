# -*- coding: utf-8 -*-
"""S06 B2 筛选：subsystem==S06 and p3b2_named=='True'，排除 fn_/sub_ 伪名，entry 升序第 19..36 行。"""
import csv, json, re
P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S06_B2\_work\b2_rows.json"
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
b2 = sel[18:36]   # 1-based #19..#36 == 0-based [18:36]
print("S06 named=True total:", len(sel_all), " pseudo excluded:", len(pseudo), " real:", len(sel))
for i, r in enumerate(sel, 1):
    mark = "*B2*" if 19 <= i <= 36 else (" B1" if i <= 18 else "   ")
    print("%2d %s %-52s %s %s size=%s call=%s site=%s valid=%s" % (
        i, r["entry"], r["name"], r["grade"], mark, r["size"], r["n_call"], r["n_site"], r["n_valid"]))
json.dump(b2, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("-> ", OUT, " rows=", len(b2))
