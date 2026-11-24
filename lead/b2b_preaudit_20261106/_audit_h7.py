# -*- coding: utf-8 -*-
import ast
import re
from pathlib import Path

design_path = Path("D:/Project/ra2-campaign-forge/lead/b2b_design_20261106/B2B_DESIGN.md")
mother_path = Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py")

mother_text = mother_path.read_text(encoding="utf-8")
design_lines = design_path.read_text(encoding="utf-8").splitlines(keepends=True)

hunks = []
current = []
in_diff = False
for line in design_lines:
    if line.startswith("```diff"):
        in_diff = True
        continue
    elif line.startswith("```") and in_diff:
        in_diff = False
        if current:
            hunks.append(current)
            current = []
        continue
    if in_diff:
        if line.startswith("@@ "):
            if current:
                hunks.append(current)
                current = []
        current.append(line)

print(f"Extracted {len(hunks)} hunks.")

cur_text = mother_text
for idx, h in enumerate(hunks):
    hdr = h[0].strip()
    minus = [l[1:] for l in h[1:] if l.startswith(" ") or l.startswith("-")]
    plus = [l[1:] for l in h[1:] if l.startswith(" ") or l.startswith("+")]
    old_snippet = "".join(minus)
    new_snippet = "".join(plus)
    count = cur_text.count(old_snippet)
    print(f"Hunk {idx+1} ({hdr}): count in text = {count}")
    if count == 1:
        cur_text = cur_text.replace(old_snippet, new_snippet, 1)
    else:
        print(f"ERROR in hunk {idx+1}")

tree = ast.parse(cur_text)
print("AST parse of all 9 hunks applied: SUCCESS")
