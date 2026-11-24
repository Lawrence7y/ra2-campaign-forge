# -*- coding: utf-8 -*-
"""S13 B1 筛选：subsystem==S13 and p3b2_named=='True'，排除 fn_/sub_ 地址式伪名，entry 升序取全部（本批 10 行）。
筛选口径完全按 a-NAMED-PUSH / NAMED-PUSH 卡面：
  subsystem == 'S13' AND p3b2_named == 'True' AND name 不是 fn_XXXXXXXX / sub_XXXXXXXX 伪名
按 entry(int,16) 升序，取全部（不足 18 就按实际数量，本批 10 行）。
"""
import csv, json, os, re
P   = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
WORK = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S13_B1\_work"
OUT  = os.path.join(WORK, "b1_rows.json")
PSEUDO = re.compile(r"^(fn_|sub_)[0-9A-Fa-f]{8}$")

rows = []
with open(P, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        rows.append(r)

s13_all  = [r for r in rows if r["subsystem"] == "S13"]
named    = [r for r in s13_all if r["p3b2_named"] == "True"]
pseudo   = [r for r in named if PSEUDO.match(r["name"])]
sel      = [r for r in named if not PSEUDO.match(r["name"])]
sel.sort(key=lambda r: int(r["entry"], 16))

print("S13 total rows in hits_detail:", len(s13_all))
print("S13 p3b2_named==True :", len(named))
print("  of which fn_/sub_ pseudo-names excluded:", len(pseudo), [r["name"] for r in pseudo])
print("S13 named non-pseudo candidates:", len(sel))
for i, r in enumerate(sel, 1):
    print("%2d %s %-28s %-14s size=%-5s call=%-3s site=%-3s valid=%s" % (
        i, r["entry"], r["name"], r["grade"], r["size"], r["n_call"], r["n_site"], r["n_valid"]))

json.dump(sel, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("count:", len(sel))
print("->", OUT)
