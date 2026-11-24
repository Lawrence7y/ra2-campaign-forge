# -*- coding: utf-8 -*-
"""筛选 S12 B2 候选：subsystem==S12 AND p3b2_named==True，排除 fn_/sub_ 伪名，
按 entry 升序取第 19..36 个（1-based）。只读 hits_detail.tsv。"""
import csv, json, os, re

P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rows_b2.json")

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
print("S12 p3b2_named=True total: %d" % len(rows))
pseudo = [r for r in rows if PSEUDO.search(r["name"])]
print("pseudo fn_/sub_ rows: %d -> %s" % (len(pseudo), [r["entry"] for r in pseudo]))
sel = [r for r in rows if not PSEUDO.search(r["name"])]
print("after exclusion: %d" % len(sel))

# 全量列出，便于确认第 19 个的边界
for i, r in enumerate(sel, 1):
    mark = "<<< B2" if 19 <= i <= 36 else ""
    print("%2d %s %-28s size=%-6s n_call=%-4s %s" % (i, r["entry"], r["name"], r["size"], r["n_call"], mark))

b2 = sel[18:36]   # 第 19..36 个（1-based）
print("\nB2 slice: %d rows  %s .. %s" % (len(b2), b2[0]["entry"], b2[-1]["entry"]))
json.dump(b2, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("->", OUT)
