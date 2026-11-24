# -*- coding: utf-8 -*-
"""M59: merge 7 PASS rows into coverage.tsv. Only cols 4/5/6 of those rows change."""
import csv, os, sys

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
D15  = os.path.join(ROOT, "S15S16_3B2", "S15_delta.tsv")
D16  = os.path.join(ROOT, "S15S16_3B2", "S16_delta.tsv")
EVID = "S15S16_3B2/_audit/VERDICT.md"

PASS = ["006E3DB0","006E4660","006E5730","006E6080","006E6410","00727240","006CE800"]

with open(COV, "r", encoding="utf-8", newline="") as f:
    raw = f.read()
assert "\r" not in raw, "unexpected CR in coverage.tsv"
lines = raw.split("\n")
trailing_lf = (lines[-1] == "")
if trailing_lf:
    lines = lines[:-1]
header = lines[0]
data = lines[1:]
assert len(data) == 18498, len(data)

# load delta col4 verbatim
delta = {}
for df in (D15, D16):
    with open(df, "r", encoding="utf-8", newline="") as f:
        rr = list(csv.reader(f, delimiter="\t"))
    for r in rr[1:]:
        if len(r) >= 6:
            delta[r[0].strip().upper()] = r[3]

# locate target rows by entry (col0)
idx = {}
for i, ln in enumerate(data):
    cols = ln.split("\t")
    assert len(cols) == 8, (i, len(cols))
    idx.setdefault(cols[0].strip().upper(), []).append(i)

for e in PASS:
    assert len(idx[e]) == 1, (e, idx.get(e))

# apply: change only col4/5/6; guard col5 currently [静态推断]
changed = []
for e in PASS:
    i = idx[e][0]
    old = data[i].split("\t")
    assert old[4] == "[静态推断]", (e, old[4])
    new = list(old)
    new[3] = delta[e]
    new[4] = "[已证]"
    new[5] = EVID
    data[i] = "\t".join(new)
    changed.append(i)

# verify byte-level: only the 7 target lines changed, and only cols 4/5/6 within them
with open(COV, "r", encoding="utf-8", newline="") as f:
    orig = f.read().split("\n")
if trailing_lf:
    orig = orig[:-1]
orig = orig[1:]
assert len(orig) == len(data)
diffs = [i for i in range(len(orig)) if orig[i] != data[i]]
assert set(diffs) == set(changed), (diffs, changed)
for i in changed:
    o = orig[i].split("\t"); n = data[i].split("\t")
    assert len(o) == len(n) == 8
    for c in (0,1,2,6,7):
        assert o[c] == n[c], (i, c)
    assert n[4] == "[已证]" and n[5] == EVID and n[3] == delta[o[0].upper()]

out = header + "\n" + "\n".join(data)
if trailing_lf:
    out += "\n"
with open(COV, "w", encoding="utf-8", newline="") as f:
    f.write(out)
print("OK: coverage.tsv updated; %d rows changed, %d data rows, header unchanged" % (len(changed), len(data)))
