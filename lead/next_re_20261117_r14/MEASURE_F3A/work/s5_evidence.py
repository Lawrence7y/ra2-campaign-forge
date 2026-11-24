# -*- coding: utf-8 -*-
"""MEASURE-F3A step 2d: what does each row's evidence_path actually point at?
A semantics proof and a *name/classification* proof live in different artifacts.
This is an independent signal, separate from the wording test.
"""
import os, re, sys, collections

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
COLS = ["entry", "subsystem", "name", "one_line_semantics",
        "grade", "evidence_path", "n_sources", "conflict"]

def load_cov():
    out = []
    with open(COV, encoding="utf-8-sig", newline="") as f:
        for i, line in enumerate(f):
            line = line.rstrip("\r\n")
            if not line:
                continue
            p = line.split("\t")
            if i == 0:
                continue
            out.append(dict(zip(COLS, p)))
    return out

rows = load_cov()
dom = [r for r in rows if r["grade"] == "[已证]"
       and "[未证]" in r["one_line_semantics"] and r["subsystem"] != "S22"]
ref = [r for r in rows if r["grade"] == "[已证]" and r["subsystem"] != "S22"]

def ev_kind(p):
    p = p.replace("\\", "/")
    first = p.split(";")[0].strip()
    base = os.path.basename(first.split("#")[0])
    return base or p

print("=== evidence artifact of the 274 F3a rows ===")
c = collections.Counter(ev_kind(r["evidence_path"]) for r in dom)
for k, v in c.most_common():
    print("%4d | %s" % (v, k))
print()
print("=== evidence artifact of ALL non-S22 [已证] rows (baseline, %d) ===" % len(ref))
c2 = collections.Counter(ev_kind(r["evidence_path"]) for r in ref)
tot = len(ref)
for k, v in c2.most_common(18):
    print("%4d (%5.1f%%) | %s" % (v, 100.0 * v / tot, k))
