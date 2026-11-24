# -*- coding: utf-8 -*-
"""_verify_design_hunks.py — 独立复核设计 §4 九 hunk 区间与 ± 计数。只读。"""
import os
import re
import difflib
import hashlib

ROOT = r"D:/Project/ra2-campaign-forge"
DESIGN = os.path.join(ROOT, "lead/b2b_design_20261106/B2B_DESIGN.md")
MOTHER = os.path.join(ROOT, "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py")
ISOL = os.path.join(ROOT, "lead/b2b_isolated_20261107/qc151_trip.isolated.py")
CANDDIFF = os.path.join(ROOT, "lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff")

text = open(DESIGN, encoding="utf-8").read()
lines = text.split("\n")
blocks, cur, inb = [], [], False
for l in lines:
    s = l.strip()
    if s == "```diff":
        inb, cur = True, []
    elif inb and s == "```":
        while cur and cur[-1] == "":
            cur.pop()
        blocks.append(cur)
        inb = False
    elif inb:
        cur.append(l)
blocks = [b for b in blocks if any(x.startswith("@@ ") for x in b)]
print("design ```diff blocks with @@ =", len(blocks))

ints = []
plus = minus = 0
for b in blocks:
    h = next(l for l in b if l.startswith("@@ "))
    g = re.match(r"@@ -(\d+),(\d+) ", h)
    ints.append((int(g.group(1)), int(g.group(2))))
    for l in b:
        if l.startswith("+") and not l.startswith("+++"):
            plus += 1
        elif l.startswith("-") and not l.startswith("---"):
            minus += 1
EXPECT = [(212, 6), (4458, 6), (4558, 8), (4572, 20), (5906, 7), (5936, 7), (6294, 6), (6386, 6), (7122, 7)]
print("design hunk intervals =", ints)
print("intervals match claim =", ints == EXPECT)
print("design hunk +/- =", plus, minus, " match +255/-13 =", (plus, minus) == (255, 13))

# independent difflib +/- count of isolated vs mother
m = open(MOTHER, "rb").read().decode("utf-8")
i = open(ISOL, "rb").read().decode("utf-8")
sm = difflib.SequenceMatcher(a=m.split("\n"), b=i.split("\n"), autojunk=False)
p = sum(j2 - j1 for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag in ("replace", "insert"))
mi = sum(i2 - i1 for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag in ("replace", "delete"))
print("independent difflib +/- =", p, mi, " match +255/-13 =", (p, mi) == (255, 13))

# CANDIDATE_LF.diff @@ count and +/- count
cd = open(CANDDIFF, "rb").read().decode("utf-8")
cl = cd.split("\n")
print("CANDIDATE_LF.diff @@ count =", sum(1 for l in cl if l.startswith("@@ ")))
cp = sum(1 for l in cl if l.startswith("+") and not l.startswith("+++"))
cm = sum(1 for l in cl if l.startswith("-") and not l.startswith("---"))
print("CANDIDATE_LF.diff +/- =", cp, cm, " match +255/-13 =", (cp, cm) == (255, 13))

# rollback diff check: isolated_vs_mother.diff vs CANDIDATE_LF.diff (only +++ b/ line should differ)
RBD = os.path.join(ROOT, "lead/b2b_isolated_20261107/_integ_isolated_vs_mother.diff")
rb = open(RBD, "rb").read()
print("rollback diff sha256 =", hashlib.sha256(rb).hexdigest(), "bytes =", len(rb), "CR =", rb.count(b"\r"))
rl = rb.decode("utf-8").split("\n")
pairs = [(n + 1, a, b) for n, (a, b) in enumerate(zip(rl, cl)) if a != b]
print("line-level diffs rollback vs CANDIDATE_LF.diff =", len(pairs), "->", [(n, a[:70], b[:70]) for n, a, b in pairs[:5]])
print("line counts rollback/canddiff =", len(rl), len(cl))
