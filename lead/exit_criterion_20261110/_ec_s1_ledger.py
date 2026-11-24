# -*- coding: utf-8 -*-
"""_ec_s1_ledger.py — 台账登记行取证（只读）。

1) GOAL_THREE_TARGETS_20261018.md 中 4 件零信息对象 + 2 件产物 out.txt 的全部登记行；
2) 指定的 5 行零信息登记行（:7569 :7634 :8383 :9588 :9679）原文（含前后 2 行上下文）；
3) PENDING_DECISIONS.md 同名扫描（确认 5 行是否只在 GOAL）。
不改任何台账。
"""
import io
import os
import re
import sys

ROOT = r"D:\Project\ra2-campaign-forge"

NAMES = [
    "_d21_burden5.py",
    "_leader_crossframe_check.py",
    "_a7_acf_probe.py",
    "_intra_frame_census.py",
    "_a7_acf_probe_out.txt",
    "_intra_frame_census_out.txt",
]
TARGET_LINES = [7569, 7634, 8383, 9588, 9679]


def scan(path, label):
    lines = io.open(path, encoding="utf-8-sig").read().splitlines()
    print("=" * 78)
    print("文件:", label, " 总行数:", len(lines))
    for name in NAMES:
        hits = [(i + 1, l) for i, l in enumerate(lines) if name in l]
        print("-" * 78)
        print("  搜「%s」→ %d 行" % (name, len(hits)))
        for ln, l in hits:
            print("    :%d| %s" % (ln, l[:220]))
    print("-" * 78)
    print("指定 5 行原文（含上下文 ±2 行）：")
    for ln in TARGET_LINES:
        print("  —— :%d —— " % ln)
        for j in range(max(0, ln - 3), min(len(lines), ln + 2)):
            mark = ">>" if (j + 1) == ln else "  "
            print("  %s:%d| %s" % (mark, j + 1, lines[j][:230]))
    return lines


def main():
    scan(os.path.join(ROOT, "lead", "GOAL_THREE_TARGETS_20261018.md"), "GOAL_THREE_TARGETS_20261018.md")
    scan(os.path.join(ROOT, "lead", "PENDING_DECISIONS.md"), "PENDING_DECISIONS.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
