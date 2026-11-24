#!/usr/bin/env python3
"""Print all S17 rows grouped by gap, UTF-8 safe to a file."""
import json, os, re, io
OUTDIR = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-K2"
with open(os.path.join(OUTDIR,"work","s17_rows.json"),encoding="utf-8") as f:
    rows = json.load(f)

def is_named(name):
    n=(name or "").strip()
    if not n: return False
    if re.fullmatch(r"sub_[0-9A-Fa-f]{8}(?:_\d+)?",n): return False
    if n.lower().startswith("sub_") and re.fullmatch(r"sub_[0-9a-fA-F]{8}.*",n): return False
    return True

out=io.StringIO()
def P(*a): print(*a,file=out)

# unnamed rows (atlas first)
P("=== UNNAMED ROWS ===")
for r in rows:
    if not is_named(r["name"]):
        P(f'{r["entry"]} atlas={r["in_atlas"]} grade={r["grade"]} name={r["name"]!r} sem={r["sem"]!r} ev={r["ev"]!r}')

P("\n=== NON-PROVED ROWS (atlas), grouped ===")
for r in rows:
    if r["in_atlas"] and r["grade"]!="[已证]":
        P(f'{r["entry"]} grade={r["grade"]} named={is_named(r["name"])} name={r["name"]!r} sem={r["sem"]!r} ev={r["ev"]!r}')

P("\n=== ALL ATLAS ROWS (entry|name|grade|sem) ===")
for r in sorted([x for x in rows if x["in_atlas"]],key=lambda x:x["entry"]):
    P(f'{r["entry"]}\t{r["name"]}\t{r["grade"]}\t{r["sem"]}')

P("\n=== OUTSIDE-ATLAS ROWS ===")
for r in rows:
    if not r["in_atlas"]:
        P(f'{r["entry"]} grade={r["grade"]} name={r["name"]!r} sem={r["sem"]!r} ev={r["ev"]!r}')

with open(os.path.join(OUTDIR,"EVIDENCE","s17_rows_report.txt"),"w",encoding="utf-8") as f:
    f.write(out.getvalue())
print("done")
