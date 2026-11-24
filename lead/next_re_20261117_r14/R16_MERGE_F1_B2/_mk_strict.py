# -*- coding: utf-8 -*-
"""Make a local copy of strict_panel.py with OUT redirected to my own product dir.
Does NOT modify the shared RULING_R15_20261119/work/strict_panel.py.
"""
import os, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
src = os.path.join(ROOT, "RULING_R15_20261119", "work", "strict_panel.py")
dst = os.path.join(ROOT, "R16_MERGE_F1_B2", "strict_panel_local.py")
s = open(src, encoding="utf-8").read()
old = 'OUT  = os.path.join(ROOT, "RULING_R15_20261119", "work")'
new = 'OUT  = os.path.join(ROOT, "R16_MERGE_F1_B2")  # B2 merge: redirected to own dir'
assert s.count(old) == 1, "OUT line count != 1"
s = s.replace(old, new, 1)
open(dst, "w", encoding="utf-8").write(s)
print("wrote", dst)
for l in s.split("\n"):
    if l.startswith("OUT "):
        print("  ", repr(l))
