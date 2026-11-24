# -*- coding: utf-8 -*-
"""M77 coverage.tsv edit: only cols 4/5/6 of the 4 audited rows.
Asserts cols 1/2/3/7/8 byte-for-byte unchanged, 18498 rows, 8 cols, LF, no BOM.
"""
import csv, os, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
DELTA = os.path.join(ROOT, "NAMED_PUSH_S07S11_B2", "delta.tsv")
TARGETS = ["006DBE00", "0069EE30", "00719E30", "0075C7F0"]
EVIDENCE = "NAMED_PUSH_AUDIT20/VERDICT.md"


def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e


with open(DELTA, encoding="utf-8-sig", newline="") as f:
    dr = list(csv.reader(f, delimiter="\t"))
dmap = {ne(r[0]): r for r in dr[1:] if r}
assert set(dmap) == set(TARGETS)

with open(COV, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8")
assert not raw.startswith(b"\xef\xbb\xbf"), "BOM"
assert "\r" not in text, "CR found"
lines = text.split("\n")
trailing = lines[-1] == ""
data = lines[1:-1] if trailing else lines[1:]
assert len(data) == 18498, len(data)
assert all(len(ln.split("\t")) == 8 for ln in data)

found = {}
for idx, ln in enumerate(data):
    p = ln.split("\t")
    if ne(p[0]) in TARGETS:
        assert ne(p[0]) not in found, "dup " + p[0]
        found[ne(p[0])] = (idx, p)
assert set(found) == set(TARGETS)

for e in TARGETS:
    idx, p = found[e]
    d = dmap[e]
    sem = d[3]
    assert "\t" not in sem and "\n" not in sem, "sem has tab/newline"
    newp = list(p)
    newp[3] = sem          # col 4 semantics = delta col4 verbatim
    newp[4] = "[已证]"       # col 5 grade
    newp[5] = EVIDENCE      # col 6 evidence_path
    # cols 1/2/3/7/8 unchanged byte-for-byte
    for k in (0, 1, 2, 6, 7):
        assert newp[k] == p[k], (e, k, p[k], newp[k])
    assert newp[4] == "[已证]" and newp[5] == EVIDENCE
    data[idx] = "\t".join(newp)
    print(f"row {e} line={idx+2}: col4/5/6 updated; cols 1/2/3/7/8 preserved")

out_lines = lines[:1] + data + ([""] if trailing else [])
out = "\n".join(out_lines)
assert len(out.split("\n")) == len(lines)
out_rows = [ln.split("\t") for ln in (out.split("\n")[1:-1] if trailing else out.split("\n")[1:])]
assert len(out_rows) == 18498 and all(len(r) == 8 for r in out_rows)

with open(COV, "wb") as f:
    f.write(out.encode("utf-8"))

print("AFTER bytes:", os.path.getsize(COV))
print("AFTER sha256:", hashlib.sha256(open(COV, "rb").read()).hexdigest())
