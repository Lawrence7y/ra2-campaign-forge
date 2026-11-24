# -*- coding: utf-8 -*-
"""MEASURE-F3A step 2c: canonicalise the boilerplate properly.

The 274 rows are one template with [未证] in two positions:
  A: 名字：YRpp/kb 地址名；归属 <类目>（名字已证，语义据名）[未证]
  B: 名字：YRpp/kb 地址名；归属 <类目>（名字已证，语义一行据名推断[未证]）
Both say exactly: name + class-belonging, nothing about behaviour.

So: strip the trailing grade-and-tail clause in all its forms, then ask whether
what is LEFT carries any byte-checkable ③b anchor.
"""
import os, re, sys, collections

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
OUT = os.path.join(ROOT, r"lead\next_re_20261117_r14\MEASURE_F3A\work")
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

rows = [r for r in load_cov()
        if r["grade"] == "[已证]" and "[未证]" in r["one_line_semantics"]
        and r["subsystem"] != "S22"]

# the self-declaring clause, in every observed spelling
TAIL = re.compile(
    r"[（(]\s*名字已证\s*[，,]\s*语义(?:一行)?据名(?:推断)?\s*(?:\[未证\])?\s*[)）]\s*(?:\[未证\])?\s*$")

def strip_tail(sem):
    m = TAIL.search(sem)
    return (sem[:m.start()], True) if m else (sem, False)

# canonical body: <name>：YRpp/kb 地址名；归属 <category>
BODY = re.compile(r"^(?P<name>[^：]+)：YRpp/kb 地址名；归属 (?P<cat>.+)$")

cats, bodies, outliers = collections.Counter(), collections.Counter(), []
for r in rows:
    core, ok = strip_tail(r["one_line_semantics"])
    if not ok:
        outliers.append(r)
        continue
    m = BODY.match(core)
    if m:
        bodies["CANON"] += 1
        cats[m.group("cat")] += 1
    else:
        outliers.append(r)

print("domain:", len(rows))
print("canonical template (name + class-belonging only):", bodies["CANON"])
print("OUTLIERS (not the bare template):", len(outliers))

print("\n===== OUTLIERS, full text =====")
for r in sorted(outliers, key=lambda r: (r["subsystem"], r["entry"])):
    core, ok = strip_tail(r["one_line_semantics"])
    print("%s\t%s\t%s" % (r["entry"], r["subsystem"], r["name"]))
    print("   tail_stripped_ok=%s" % ok)
    print("   core=%s" % core)
    print("   sem =%s" % r["one_line_semantics"])
    print("   ev  =%s" % r["evidence_path"])

print("\n===== canonical 'cat' tally =====")
for k, v in cats.most_common():
    print("%3d | %s" % (v, k))
