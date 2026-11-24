# -*- coding: utf-8 -*-
"""MEASURE-F3A step 10: reconcile the 317 with the card's three wording classes."""
import os, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge"
COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
COLS = ["entry", "subsystem", "name", "one_line_semantics",
        "grade", "evidence_path", "n_sources", "conflict"]
rows = []
for i, line in enumerate(open(COV, encoding="utf-8-sig", newline="")):
    line = line.rstrip("\r\n")
    if not line or i == 0:
        continue
    rows.append(dict(zip(COLS, line.split("\t"))))

f3a = [r for r in rows if r["grade"] == "[已证]" and "[未证]" in r["one_line_semantics"]]

def cls(r):
    s = r["one_line_semantics"]
    s22 = r["subsystem"] == "S22"
    if "语义一行据名推断" in s:
        return ("B_语义一行据名推断", s22)
    if "名字已证" in s and "语义据名" in s:
        return ("A_语义据名", s22)
    if "S22" in s or "兜底" in s or "无法归类" in s:
        return ("C_S22兜底", s22)
    return ("D_其它", s22)

c = collections.Counter(cls(r) for r in f3a)
print("317-row composition (class, is_S22) -> count")
for k in sorted(c):
    print("  %-24s S22=%-5s %4d" % (k[0], k[1], c[k]))

n_nons22 = sum(v for (k, s22), v in c.items() if not s22)
print("\nnon-S22 total:", n_nons22)
print("S22 total    :", sum(v for (k, s22), v in c.items() if s22))

a_ns = c.get(("A_语义据名", False), 0)
a_s = c.get(("A_语义据名", True), 0)
b_ns = c.get(("B_语义一行据名推断", False), 0)
b_s = c.get(("B_语义一行据名推断", True), 0)
d_ns = c.get(("D_其它", False), 0)
d_s = c.get(("D_其它", True), 0)
e_s = c.get(("C_S22兜底", True), 0)
print("\nreconciliation with the card's 317 = 213 + 65 + 39:")
print("  213 = A everywhere (%d non-S22 + %d S22) = %d  %s"
      % (a_ns, a_s, a_ns + a_s, "OK" if a_ns + a_s == 213 else "MISMATCH"))
print("   65 = other wording, non-S22 only (B %d + D %d) = %d  %s"
      % (b_ns, d_ns, b_ns + d_ns, "OK" if b_ns + d_ns == 65 else "MISMATCH"))
print("   39 = S22 兜底 = %d  %s" % (e_s, "OK" if e_s == 39 else "MISMATCH"))
print("  total 213+65+39 = %d  vs 317  %s"
      % (213 + 65 + 39, "OK" if 213 + 65 + 39 == 317 else "MISMATCH"))
print("  non-S22 = %d  (card says 274)  %s"
      % (a_ns + b_ns + d_ns, "OK" if a_ns + b_ns + d_ns == 274 else "MISMATCH"))
print("  S22 remainder (B/D inside S22) = %d" % (b_s + d_s))

# per-subsystem distribution cross-check against the card
dist = collections.Counter(r["subsystem"] for r in f3a if r["subsystem"] != "S22")
card = {"S15": 53, "S05": 32, "S02": 30, "S16": 26, "S07": 23, "S09": 17,
        "S06": 15, "S12": 15, "S10": 14, "S14": 13, "S20": 12, "S18": 10,
        "S19": 9, "S03": 2, "S11": 1, "S13": 1, "S17": 1}
print("\nper-subsystem vs card: %s" % ("IDENTICAL" if dict(dist) == card else "DIFF"))
if dict(dist) != card:
    print(" mine:", dict(sorted(dist.items())))
    print(" card:", dict(sorted(card.items())))
