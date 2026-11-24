# -*- coding: utf-8 -*-
"""筛选命令的可复算落盘：S18 中 p3b2_named==True 且名字非 fn_/sub_ 伪名的候选，
按 entry 升序取第 37..54（0-based [36:54]）。卡片新增规则：排除地址式伪名。"""
import csv, os, json, re
R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
HITS = os.path.join(R14, "SURVEY_3B2", "hits_detail.tsv")
WORK = os.path.dirname(os.path.abspath(__file__))

rows = []
with open(HITS, encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        rows.append(r)

named_all = sorted([r for r in rows if r["subsystem"] == "S18" and r["p3b2_named"] == "True"],
                   key=lambda x: int(x["entry"], 16))

PSEUDO = re.compile(r'^(fn_|sub_)[0-9A-Fa-f]{8}$')
def is_pseudo(name):
    return bool(PSEUDO.match(name))

pseudo = [r for r in named_all if is_pseudo(r["name"])]
named = [r for r in named_all if not is_pseudo(r["name"])]

print("S18 named=True total:", len(named_all))
print("  pseudo fn_/sub_ excluded:", len(pseudo))
for r in pseudo:
    print("    PSEUDO", r["entry"], r["name"])
print("S18 named=True non-pseudo:", len(named))
b3 = named[36:54]   # 第 37..54 个（1-based）
print("B3 rows:", len(b3))
for i, r in enumerate(b3, 37):
    print("%2d %s %-6s %-55s size=%s" % (i, r["entry"], r["subsystem"], r["name"], r["size"]))

# 对照：若不排除伪名，第 37..54 会是什么（用于核对批次衔接）
print("\n--- comparison: WITHOUT exclusion [36:54] ---")
for i, r in enumerate(named_all[36:54], 37):
    print("%2d %s %-55s%s" % (i, r["entry"], r["name"], "  <PSEUDO>" if is_pseudo(r["name"]) else ""))

with open(os.path.join(WORK, "b3_rows.json"), "w", encoding="utf-8") as f:
    json.dump(b3, f, ensure_ascii=False, indent=1)
print("\nwrote b3_rows.json (%d rows)" % len(b3))
