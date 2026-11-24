# -*- coding: utf-8 -*-
"""筛选命令的可复算落盘：S07 中 p3b2_named==True 且非 fn_/sub_ 伪名的候选按 entry 升序取前 18。"""
import csv, os, json, re
R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
HITS = os.path.join(R14, "SURVEY_3B2", "hits_detail.tsv")
WORK = os.path.dirname(os.path.abspath(__file__))

rows = []
with open(HITS, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        rows.append(r)

named = [r for r in rows if r["subsystem"] == "S07" and r["p3b2_named"] == "True"]
def is_pseudo(n):
    return bool(re.match(r"^(fn_|sub_)[0-9A-Fa-f]{8}$", n))
real = [r for r in named if not is_pseudo(r["name"])]
b1 = sorted(real, key=lambda x: int(x["entry"], 16))[:18]

print("S07 named=True total:", len(named))
print("after excluding fn_/sub_ pseudo:", len(real))
for i, r in enumerate(b1, 1):
    print("%2d %s %s %s size=%s" % (i, r["entry"], r["subsystem"], r["name"], r["size"]))

with open(os.path.join(WORK, "b1_rows.json"), "w", encoding="utf-8") as f:
    json.dump(b1, f, ensure_ascii=False, indent=1)
print("wrote b1_rows.json (%d rows)" % len(b1))
