# -*- coding: utf-8 -*-
"""Final: PANEL.md tables vs authoritative strict_panel.tsv (all rows)."""
import csv, sys
sys.stdout.reconfigure(encoding="utf-8")
P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\PANEL.md"
SP = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\MERGE_M66\_strict_out\strict_panel.tsv"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\MERGE_M66\_final_check.txt"

lines = open(P, encoding="utf-8").read().split("\n")
auth = {}
with open(SP, encoding="utf-8") as f:
    r = csv.reader(f, delimiter="\t")
    next(r)
    for row in r:
        auth[row[0]] = dict(atlas=int(row[1]), proved=int(row[5]), strict=int(row[6]))

results = []
for idx in range(54, 76):
    c = [x.strip().replace("*", "") for x in lines[idx].split("|")]
    s = c[1]; atlas = int(c[2]); proved = int(c[9]); a = auth[s]
    results.append((f"main {s}", atlas==a["atlas"] and proved==a["proved"],
                    f"{atlas}/{proved} vs {a['atlas']}/{a['proved']}"))
for idx in range(104, 126):
    c = [x.strip().replace("*", "") for x in lines[idx].split("|")]
    s = c[1]; atlas = int(c[2]); proved = int(c[3]); strict = int(c[5]); a = auth[s]
    results.append((f"strict {s}", atlas==a["atlas"] and proved==a["proved"] and strict==a["strict"],
                    f"{atlas}/{proved}/{strict} vs {a['atlas']}/{a['proved']}/{a['strict']}"))

with open(OUT,"w",encoding="utf-8") as f:
    f.write("FINAL CONSISTENCY CHECK: PANEL.md tables vs authoritative strict_panel.tsv\n")
    f.write("="*70+"\n")
    allok = True
    for name, ok, detail in results:
        f.write(("PASS" if ok else "FAIL")+f"  {name}: {detail}\n")
        allok &= ok
    f.write("\nALL CONSISTENT: %s\n" % allok)
print("wrote", OUT, "allok=", allok)
