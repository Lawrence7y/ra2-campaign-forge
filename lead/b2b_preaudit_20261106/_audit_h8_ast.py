# -*- coding: utf-8 -*-
from pathlib import Path
import ast

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

print(f"Total hunks extracted: {len(hunks)}")
h8 = hunks[7]
hdr = h8[0].strip()
print(f"Hunk 8 header: {hdr}")
minus = "".join([l[1:] for l in h8[1:] if l.startswith(" ") or l.startswith("-")])
plus = "".join([l[1:] for l in h8[1:] if l.startswith(" ") or l.startswith("+")])

cnt = mother_text.count(minus)
print(f"Minus snippet occurrence in mother file: {cnt}")
assert cnt == 1

patched_h8_only = mother_text.replace(minus, plus, 1)
ast.parse(patched_h8_only)
print("Single H8 patch AST parse: SUCCESS")

# Now apply all 9 hunks sequentially and check
cur = mother_text
for i, h in enumerate(hunks):
    m = "".join([l[1:] for l in h[1:] if l.startswith(" ") or l.startswith("-")])
    p = "".join([l[1:] for l in h[1:] if l.startswith(" ") or l.startswith("+")])
    assert cur.count(m) == 1, f"Hunk {i+1} minus match failed!"
    cur = cur.replace(m, p, 1)

ast.parse(cur)
print("All 9 hunks patch AST parse: SUCCESS")
