# -*- coding: utf-8 -*-
"""Independent reviewer: re-read ledger anchors used by handoff + 104 literal search + mtime of protected files."""
import os, re, time

BASE = r"D:/Project/ra2-campaign-forge"
LEDGER = "lead/GOAL_THREE_TARGETS_20261018.md"
PENDING = "lead/PENDING_DECISIONS.md"

def lines_of(rel):
    with open(os.path.join(BASE, rel), "r", encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()

print("=== GOAL anchors re-read ===")
L = lines_of(LEDGER)
for ln in [53, 5828, 6018, 6019, 6020, 6030, 6032, 6035, 6040, 6053, 6055,
           6065, 6066, 6068, 6069, 6642, 6646, 7095, 7099, 8408, 8414,
           4391, 5140, 5155, 9740, 9741, 9745, 9746, 9747, 9751, 9756]:
    if 1 <= ln <= len(L):
        print("GOAL:%d: %s" % (ln, L[ln-1][:260]))
    else:
        print("GOAL:%d: <OUT OF RANGE, total %d lines>" % (ln, len(L)))

print()
print("=== PENDING :15-75 (selected) ===")
P = lines_of(PENDING)
for ln in [23, 24, 25, 34, 40, 47, 63, 64, 74]:
    if 1 <= ln <= len(P):
        print("PENDING:%d: %s" % (ln, P[ln-1][:260]))

print()
print("=== independent '104 件' literal search over 6 files ===")
files = [
    "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md",
    "lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md",
    "lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md",
    "lead/re_line_20261105/D24_RULING/RULING_D24.md",
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
]
for rel in files:
    try:
        LL = lines_of(rel)
    except FileNotFoundError:
        print("-- %s : MISSING" % rel)
        continue
    lit = [i for i, t in enumerate(LL, 1) if ("104 件" in t) or ("104件" in t)]
    num = [i for i, t in enumerate(LL, 1) if re.search(r"(?<![0-9A-Za-z_])104(?![0-9])", t)]
    ctx = [ (i, LL[i-1][:160]) for i in num if ("measure" in LL[i-1] or "语料" in LL[i-1] or "文件数" in LL[i-1]) ]
    print("-- %s : literal'104 件'=%s ; numeric104_lines=%d" % (rel, lit if lit else "无", len(num)))
    for i, t in ctx[:6]:
        print("     %d: %s" % (i, t))

print()
print("=== protected files mtime (read-only stat) ===")
protected = [
    "lead/GOAL_THREE_TARGETS_20261018.md",
    "lead/PENDING_DECISIONS.md",
    "lead/re_line_20261105/D24_RULING/RULING_D24.md",
    "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md",
    "lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md",
    "lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md",
]
for rel in protected:
    p = os.path.join(BASE, rel)
    st = os.stat(p)
    print("%s  size=%d  mtime=%s" % (rel, st.st_size, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))))
