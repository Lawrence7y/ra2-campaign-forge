# -*- coding: utf-8 -*-
"""筛选本批候选：subsystem in (S16, S21) AND p3b2_named==True，再排除 fn_/sub_ 伪名，按 entry 升序。"""
import csv, os, json

BASE = r"D:\Project\ra2-campaign-forge"
P = os.path.join(BASE, r"lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv")
SUBS = ("S16", "S21")

named_all, rows, dropped = [], [], []
with open(P, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        if row["subsystem"] in SUBS and row["p3b2_named"] == "True":
            named_all.append(row)
            n = row["name"]
            if n.startswith("fn_") or n.startswith("sub_"):
                dropped.append(row)
                continue
            rows.append(row)

rows.sort(key=lambda x: (x["subsystem"], int(x["entry"], 16)))

print("named=True rows: %d ; dropped pseudo-names: %d ; candidates: %d"
      % (len(named_all), len(dropped), len(rows)))
for s in SUBS:
    print("  %s named=%d kept=%d" % (s,
          sum(1 for r in named_all if r["subsystem"] == s),
          sum(1 for r in rows if r["subsystem"] == s)))
print()
print("%-10s %-5s %-32s %-6s %6s %6s" % ("entry", "sub", "name", "grade", "size", "ninsn"))
for r in rows:
    print("%-10s %-5s %-32s %-6s %6s %6s"
          % (r["entry"], r["subsystem"], r["name"], r["grade"], r["size"], r["n_insn"]))

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "candidates.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)
print("\n-> %s" % out)
