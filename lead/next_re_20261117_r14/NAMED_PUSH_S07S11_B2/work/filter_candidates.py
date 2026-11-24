# -*- coding: utf-8 -*-
"""NAMED_PUSH_S07S11_B2 候选筛选（可复算落盘）。

从 SURVEY_3B2/hits_detail.tsv 取 subsystem∈{S07,S11} 且 p3b2_named==True 的行，
排除 fn_/sub_ 地址式伪名，按 entry 升序，减去 NAMED_PUSH_S07_B1 / S11_B1 已核的 18 行，
剩下的即本批（S07 4 行 + S11 11 行）。
"""
import csv, os, json, re

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
HITS = os.path.join(R14, "SURVEY_3B2", "hits_detail.tsv")
B1_S07 = os.path.join(R14, "NAMED_PUSH_S07_B1", "work", "b1_rows.json")
B1_S11 = os.path.join(R14, "NAMED_PUSH_S11_B1", "work", "b1_rows.json")
WORK = os.path.dirname(os.path.abspath(__file__))


def is_pseudo(n):
    return bool(re.match(r"^(fn_|sub_)[0-9A-Fa-f]{8}$", n.split("::")[-1])) \
        or bool(re.match(r"^(fn_|sub_)[0-9A-Fa-f]{8}$", n))


rows = list(csv.DictReader(open(HITS, encoding="utf-8"), delimiter="\t"))

result = {}
for sub in ("S07", "S11"):
    named = [r for r in rows if r["subsystem"] == sub and r["p3b2_named"] == "True"]
    pseudo = [r for r in named if is_pseudo(r["name"])]
    real = [r for r in named if not is_pseudo(r["name"])]
    real.sort(key=lambda x: int(x["entry"], 16))
    b1 = json.load(open(B1_S07 if sub == "S07" else B1_S11, encoding="utf-8"))
    b1_entries = {r["entry"].upper() for r in b1}
    remain = [r for r in real if r["entry"].upper() not in b1_entries]

    print("=== %s ===" % sub)
    print("named=True total       :", len(named))
    print("  pseudo fn_/sub_       :", len(pseudo), [r["name"] for r in pseudo])
    print("  real (non-pseudo)     :", len(real))
    print("  B1 checked            :", len(b1))
    print("  remaining for B2      :", len(remain))
    for i, r in enumerate(remain, 1):
        print("   %2d %s  %-48s size=%s" % (i, r["entry"], r["name"], r["size"]))
    result[sub] = remain

with open(os.path.join(WORK, "candidates.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("\nwrote candidates.json")
