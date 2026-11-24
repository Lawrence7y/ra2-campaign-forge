# -*- coding: utf-8 -*-
"""S22 B1 筛选：subsystem==S22 AND p3b2_named==True，排除 fn_/sub_ 伪名，按 entry 升序取前 18。"""
import csv, os, json, re

HITS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
OUT  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "b1_rows.json")

FN = re.compile(r"^fn_[0-9A-Fa-f]{8}$")
SUB = re.compile(r"^sub_[0-9A-Fa-f]{8}$")

def main():
    with open(HITS, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    named = [r for r in rows if r["subsystem"].strip() == "S22" and r["p3b2_named"].strip() == "True"]
    kept = [r for r in named if not FN.match(r["name"].strip()) and not SUB.match(r["name"].strip())]
    kept.sort(key=lambda r: int(r["entry"], 16))
    sel = kept[:18]
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"s22_named_all": len(named), "s22_named_kept": len(kept), "rows": sel}, f, ensure_ascii=False, indent=1)
    print("S22 named=True =", len(named), "; after fn_/sub_ exclusion =", len(kept), "; selected =", len(sel))
    for i, r in enumerate(sel, 1):
        print("%2d %s %-60s size=%s" % (i, r["entry"], r["name"], r["size"]))

if __name__ == "__main__":
    main()
