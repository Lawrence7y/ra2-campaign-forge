# -*- coding: utf-8 -*-
"""Dump relevant PANEL.md lines with line numbers."""
import os, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
lines = open(PANEL, encoding="utf-8").read().split("\n")
print("PANEL total lines:", len(lines))
print("="*80)
# title
print("TITLE line 1:", repr(lines[0][:300]))
print("="*80)
keys = ["全表 `[已证]`", "| S03 |", "| S06 |", "| S16 |", "| S21 |", "| **TOTAL** |",
        "M75 披露", "M74 披露", "M75 并表实算说明", "备注"]
for i,l in enumerate(lines, start=1):
    for k in keys:
        if k in l:
            print(f"L{i}: {l[:400]}")
            break
