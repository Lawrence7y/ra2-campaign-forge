# -*- coding: utf-8 -*-
"""NAMED-PUSH S18 B4 筛选：S18 & p3b2_named==True & 非 fn_/sub_ 伪名，
减去 B1/B2/B3 已核 54 行，按 entry 升序取前 18。落 b4_rows.json。"""
import csv, os, json

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
HITS = os.path.join(BASE, r"SURVEY_3B2\hits_detail.tsv")
WORK = os.path.dirname(os.path.abspath(__file__))

checked = set()
for b in ("B1", "B2", "B3"):
    d = os.path.join(BASE, f"NAMED_PUSH_S18_{b}", "EVIDENCE")
    for f in os.listdir(d):
        if f.startswith("ROW_") and f.endswith(".txt"):
            checked.add(f[4:-4].upper())

rows = []
with open(HITS, encoding="utf-8") as fh:
    for r in csv.DictReader(fh, delimiter="\t"):
        if r["subsystem"] != "S18" or r["p3b2_named"] != "True":
            continue
        name = r["name"]
        if name.startswith("fn_") or name.startswith("sub_"):
            continue
        e = r["entry"].strip().upper()
        rows.append({"entry": e, "subsystem": "S18", "name": name, "grade": r["grade"]})

rows.sort(key=lambda x: int(x["entry"], 16))
rem = [r for r in rows if r["entry"] not in checked]
sel = rem[:18]

json.dump({"all_named_nonpseudo": len(rows), "checked": len(checked),
           "remaining": len(rem), "selected": sel, "rest_pool": rem[18:]},
          open(os.path.join(WORK, "b4_rows.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("all=%d checked=%d remaining=%d selected=%d rest=%d" % (
    len(rows), len(checked), len(rem), len(sel), len(rem) - 18))
for i, r in enumerate(sel, 1):
    print("%2d %s %s" % (i, r["entry"], r["name"]))
