# -*- coding: utf-8 -*-
import ast
import sys
from pathlib import Path

# Load mother file
mother_path = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py")
mother_text = mother_path.read_text(encoding="utf-8")
mother_lines = mother_text.splitlines(keepends=True)

# Load design file
design_path = Path(r"D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\B2B_DESIGN.md")
design_lines = design_path.read_text(encoding="utf-8").splitlines(keepends=True)

# Extract H4
h4_start = None
for i, l in enumerate(design_lines):
    if l.startswith("@@ -4572,20"):
        h4_start = i
        break

h4_diff = []
for i in range(h4_start + 1, len(design_lines)):
    l = design_lines[i]
    if l.startswith("```"):
        break
    h4_diff.append(l)

# Construct replacement text for H4
# Minus/context: lines 4572..4591 (1-based: 4571..4591)
# Replacement: plus lines + context lines in their places
plus_and_ctx = []
for l in h4_diff:
    if l.startswith(" ") or l.startswith("+"):
        plus_and_ctx.append(l[1:])

# Replace in mother lines (just H4 replacement to check syntax/ast of the function)
# Note: we need H1 (constants) and H3 (definitions and signature) for full syntax/resolution,
# but let's test H4 replacement inside copy_post_except_evidence.
test_lines = mother_lines[:4571] + plus_and_ctx + mother_lines[4591:]
test_code = "".join(test_lines)

try:
    tree = ast.parse(test_code)
    print("ast.parse with H4 applied to mother: SUCCESS!")
except SyntaxError as e:
    print("SyntaxError:", e)
