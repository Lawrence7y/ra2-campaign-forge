# -*- coding: utf-8 -*-
import sys
from pathlib import Path

design_path = Path(r"D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\B2B_DESIGN.md")
mother_path = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py")

with open(design_path, "r", encoding="utf-8") as f:
    design_lines = f.readlines()

with open(mother_path, "r", encoding="utf-8") as f:
    mother_lines = f.readlines()

# Locate H4
h4_start = None
for i, line in enumerate(design_lines):
    if line.startswith("@@ -4572,20"):
        h4_start = i
        break

assert h4_start is not None, "H4 not found!"
print("Found H4 at line", h4_start + 1, ":", repr(design_lines[h4_start]))

h4_diff = []
for i in range(h4_start + 1, len(design_lines)):
    line = design_lines[i]
    if line.startswith("```"):
        break
    h4_diff.append(line)

print("H4 diff lines count:", len(h4_diff))

mother_idx = 4571 # 4572 1-based
diff_minus_and_ctx = []
diff_plus = []

for dl in h4_diff:
    prefix = dl[0]
    content = dl[1:]
    if prefix in (" ", "-"):
        diff_minus_and_ctx.append((prefix, content))
    elif prefix == "+":
        diff_plus.append(content)

print(f"Minus/Context lines count: {len(diff_minus_and_ctx)}")
print(f"Plus lines count: {len(diff_plus)}")

all_matched = True
for idx, (pfx, text) in enumerate(diff_minus_and_ctx):
    m_line = mother_lines[mother_idx + idx]
    match = (m_line == text)
    if not match:
        all_matched = False
        print(f"MISMATCH at mother line {mother_idx + idx + 1}:")
        print("  DIFF:  ", repr(text))
        print("  MOTHER:", repr(m_line))
    else:
        print(f"Line {mother_idx + idx + 1:4d} [{pfx}]: OK - {m_line.strip()[:60]}")

print("All -/context lines matched exactly?", all_matched)
