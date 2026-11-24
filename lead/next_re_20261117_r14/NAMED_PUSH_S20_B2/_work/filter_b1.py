# -*- coding: utf-8 -*-
"""S20 B1 候选筛选：S20 AND p3b2_named==True，排除 fn_/sub_ 伪名，entry 升序取前 18。

卡片 NAMED-PUSH 的筛选条件逐条落地；产物 b1_rows.json 供后续脚本使用。
"""
import csv, json, os, re

BASE = r"D:\Project\ra2-campaign-forge"
SRC = os.path.join(BASE, r"lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv")
WORK = os.path.dirname(os.path.abspath(__file__))

PSEUDO = re.compile(r"^(?:[A-Za-z0-9_<>@$?]*::)?(?:fn|sub)_[0-9A-Fa-f]{8}$")


def main():
    rows = []
    with open(SRC, encoding="utf-8-sig") as f:
        rdr = csv.DictReader(f, delimiter="\t")
        for r in rdr:
            rows.append(r)

    named = [r for r in rows if r["subsystem"] == "S20" and r["p3b2_named"] == "True"]
    named.sort(key=lambda r: int(r["entry"], 16))

    pseudo = [r for r in named if PSEUDO.match(r["name"])]
    clean = [r for r in named if not PSEUDO.match(r["name"])]
    b1 = clean[:18]

    print("S20 total rows        : %d" % len([r for r in rows if r["subsystem"] == "S20"]))
    print("S20 p3b2_named==True  : %d" % len(named))
    print("  伪名 fn_/sub_        : %d" % len(pseudo))
    print("  排除伪名后           : %d" % len(clean))
    print("B1 = 升序前 18         : %d" % len(b1))
    for i, r in enumerate(b1, 1):
        print("  %2d %s %-32s %s" % (i, r["entry"], r["name"], r["grade"]))

    json.dump(b1, open(os.path.join(WORK, "b1_rows.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    # 存档一份纯 entry 列表，便于报告引用
    with open(os.path.join(WORK, "b1_entries.txt"), "w", encoding="utf-8") as f:
        for r in b1:
            f.write("%s\t%s\n" % (r["entry"], r["name"]))


if __name__ == "__main__":
    main()
