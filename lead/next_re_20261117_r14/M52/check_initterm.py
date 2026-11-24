# -*- coding: utf-8 -*-
"""Count initterm-class rows in coverage.tsv; verify caliber B/C identity."""
import re, collections
COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
with open(COV, "r", encoding="utf-8-sig", newline="") as f:
    lines = f.read().split("\n")
while lines and lines[-1] == "":
    lines.pop()
rows = [ln.split("\t") for ln in lines[1:]]

# initterm_thunk_NNNN by name
it_name = [r for r in rows if re.match(r"^initterm_thunk_\d+$", r[2].strip())]
print("rows with name initterm_thunk_NNNN:", len(it_name))
print("  grade hist:", dict(collections.Counter(r[4] for r in it_name)))
print("  subsystem hist:", dict(collections.Counter(r[1] for r in it_name)))

# evidence_path containing P0_INITTERM or initterm
it_ev = [r for r in rows if "initterm" in r[5].lower()]
print("rows with evidence_path containing 'initterm':", len(it_ev))

# semantics containing initterm
it_sem = [r for r in rows if "initterm" in r[3].lower()]
print("rows with semantics containing 'initterm':", len(it_sem))

# names by prefix family
pref = collections.Counter()
for r in rows:
    n = r[2].strip()
    if n.startswith("initterm_thunk_"):
        pref["initterm_thunk_"] += 1
    elif n.startswith("sub_"):
        pref["sub_"] += 1
    else:
        pref["other"] += 1
print("name prefix families:", dict(pref))

# P0 closure rows: semantics contains 'P0 入口闭合用'
p0close = [r for r in rows if "P0 入口闭合用" in r[3]]
print("rows with 'P0 入口闭合用' in semantics:", len(p0close),
      "all S22:", all(r[1].strip()=="S22" for r in p0close))

# B per §9.1 = coverage - initterm(thunks) = 18498 - X
X = len(it_name)
print("\ncoverage rows:", len(rows))
print("initterm thunk rows:", X)
print("B = coverage - initterm =", len(rows) - X)
print("C = coverage =", len(rows))
print("identity B + X = C:", (len(rows)-X) + X == len(rows))
