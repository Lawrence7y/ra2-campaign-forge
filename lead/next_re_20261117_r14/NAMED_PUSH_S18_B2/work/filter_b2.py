# -*- coding: utf-8 -*-
"""筛选命令的可复算落盘：S18 中 p3b2_named==True 的候选按 entry 升序取第 19..36（0-based [18:36]）。"""
import csv, os, json
R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
HITS = os.path.join(R14, "SURVEY_3B2", "hits_detail.tsv")
WORK = os.path.dirname(os.path.abspath(__file__))

rows = []
with open(HITS, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        rows.append(r)

named = sorted([r for r in rows if r["subsystem"] == "S18" and r["p3b2_named"] == "True"],
               key=lambda x: int(x["entry"], 16))
b2 = named[18:36]   # 第 19..36 个（1-based）

print("S18 named=True total:", len(named))
for i, r in enumerate(b2, 19):
    print("%2d %s %s %s size=%s" % (i, r["entry"], r["subsystem"], r["name"], r["size"]))

with open(os.path.join(WORK, "b2_rows.json"), "w", encoding="utf-8") as f:
    json.dump(b2, f, ensure_ascii=False, indent=1)
print("wrote b2_rows.json (%d rows)" % len(b2))
