#!/usr/bin/env python3
"""Verify the §825-8 -> §825-9 sync changed ONLY that block.

Compares the pre-sync backup with the current ledger after normalising line
endings (the sync rewrote CRLF as LF; the original file was mixed).
"""
import difflib
import io

CUR = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
BAK = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W127_reach\GOAL_backup_before_825_9.md"


def norm(p):
    b = open(p, "rb").read()
    s = b.decode("utf-8")
    return s.replace("\r\n", "\n").split("\n")


a, b = norm(BAK), norm(CUR)
print("backup lines=%d  current lines=%d" % (len(a), len(b)))
sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
n_add = n_del = 0
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        continue
    n_del += i2 - i1
    n_add += j2 - j1
    print("\n[%s] backup %d..%d -> current %d..%d" % (tag, i1, i2, j1, j2))
    for line in a[i1:i2][:12]:
        print("   -" + line[:110])
    for line in b[j1:j2][:20]:
        print("   +" + line[:110])
print("\ntotal removed=%d added=%d" % (n_del, n_add))
