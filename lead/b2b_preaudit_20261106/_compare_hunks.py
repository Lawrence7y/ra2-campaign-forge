# -*- coding: utf-8 -*-
import ast
import re
from pathlib import Path

design_path = Path(r"D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\B2B_DESIGN.md")
draft_path = Path(r"D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\_draft_semantics.md")
mother_path = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py")

mother_lines = mother_path.read_text(encoding="utf-8").splitlines(keepends=True)

def extract_hunks(md_path):
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    hunks = []
    current = None
    in_diff = False
    for line in lines:
        if line.startswith("```diff"):
            in_diff = True
            continue
        elif line.startswith("```") and in_diff:
            in_diff = False
            if current:
                hunks.append(current)
                current = None
            continue
        if in_diff:
            if line.startswith("@@ "):
                if current:
                    hunks.append(current)
                current = [line]
            elif current is not None:
                current.append(line)
    if current:
        hunks.append(current)
    return hunks

b2b_hunks = extract_hunks(design_path)
draft_hunks = extract_hunks(draft_path)

print(f"B2B_DESIGN.md hunks: {len(b2b_hunks)}")
print(f"_draft_semantics.md hunks: {len(draft_hunks)}")

for i in range(len(b2b_hunks)):
    h_b2b = b2b_hunks[i]
    h_draft = draft_hunks[i]
    match = (h_b2b == h_draft)
    print(f"Hunk {i+1} header: {h_b2b[0].strip()} - matches draft: {match}")

# Specifically check H4 (index 3)
h4 = b2b_hunks[3]
print("\nH4 details:")
print("Header:", h4[0].strip())
print("Total lines in hunk:", len(h4))
