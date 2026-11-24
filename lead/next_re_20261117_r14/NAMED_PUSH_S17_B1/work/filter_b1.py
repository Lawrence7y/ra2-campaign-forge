# -*- coding: utf-8 -*-
"""候选筛选 + SHA256 自校验（NAMED_PUSH_S17_B1）。"""
import csv, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import np_core as C

P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"

def filter_rows():
    named_all, rows = [], []
    with open(P, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if row["subsystem"] == "S17" and row["p3b2_named"] == "True":
                named_all.append(row)
                n = row["name"]
                if n.startswith("fn_") or n.startswith("sub_"):
                    continue
                rows.append(row)
    rows.sort(key=lambda x: int(x["entry"], 16))
    return named_all, rows

if __name__ == "__main__":
    sha = C.sha256_exe()
    print("exe sha256 =", sha)
    print("sha match =", sha == C.EXPECT_SHA)
    named_all, rows = filter_rows()
    print("S17 named=True total:", len(named_all))
    pseudo = [r["entry"] for r in named_all if r["name"].startswith(("fn_", "sub_"))]
    print("pseudo excluded:", pseudo)
    print("real-name candidates:", len(rows))
    for i, r in enumerate(rows[:18], 1):
        print(i, r["entry"], r["name"], "size=" + r["size"])
