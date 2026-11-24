# -*- coding: utf-8 -*-
"""MEASURE-F3A step 2a: dump the 274-row domain with wording normalisation,
so the (甲)/(乙) criteria can be read off the actual text instead of guessed.
"""
import json, os, sys, collections, re

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
            parts = line.split("\t")
            if i == 0:
                continue
            out.append(dict(zip(COLS, parts)))
    return out

rows = load_cov()
f3a = [r for r in rows if r["grade"] == "[已证]" and "[未证]" in r["one_line_semantics"]]
print("total F3a (all subs):", len(f3a))
dom = [r for r in f3a if r["subsystem"] != "S22"]
print("domain (non-S22):", len(dom))

# ---- wording classes: how does the [未证] tail present?
def tail_class(sem):
    if re.search(r"[（(]名字已证[，,]语义[^）)]*[)）]\[未证\]$", sem):
        return "W1_名字已证语义据名推断"
    if "S22" in sem:
        return "W3_S22兜底"
    return "W2_其它"

cls = collections.Counter(tail_class(r["one_line_semantics"]) for r in f3a)
print("wording classes over all 317:", dict(cls))
cls2 = collections.Counter(tail_class(r["one_line_semantics"]) for r in dom)
print("wording classes over 274:", dict(cls2))

# S22's own wording breakdown
s22 = [r for r in f3a if r["subsystem"] == "S22"]
print("S22 count:", len(s22), dict(collections.Counter(tail_class(r['one_line_semantics']) for r in s22)))
for r in s22[:50]:
    if tail_class(r["one_line_semantics"]) != "W3_S22兜底":
        print("  S22 non-W3:", r["entry"], "|", r["one_line_semantics"][:120])

# ---- show distinct [未证] tail shapes among the 274, grouped by the 40 chars before it
tails = collections.Counter()
for r in dom:
    s = r["one_line_semantics"]
    i = s.rfind("[未证]")
    tails[s[max(0, i-46):i+4]] += 1
print("\n--- distinct tails (274 domain), top 40 ---")
for t, n in tails.most_common(40):
    print("%3d | %s" % (n, t))

# write raw dump for eyeballing
with open(os.path.join(OUT, "s2_domain_raw.txt"), "w", encoding="utf-8") as f:
    for r in sorted(dom, key=lambda r: (r["subsystem"], r["entry"])):
        f.write("%s\t%s\t%s\t%s\n" % (r["entry"], r["subsystem"], r["name"], r["one_line_semantics"]))
print("\nwrote s2_domain_raw.txt")
