# -*- coding: utf-8 -*-
import ast
from pathlib import Path

design_path = Path("D:/Project/ra2-campaign-forge/lead/b2b_design_20261106/B2B_DESIGN.md")
mother_path = Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py")

mother_lines = mother_path.read_text(encoding="utf-8").splitlines(keepends=True)
design_lines = design_path.read_text(encoding="utf-8").splitlines(keepends=True)

# 1. Locate H8 in B2B_DESIGN.md
h8_lines = []
in_h8 = False
for i, line in enumerate(design_lines):
    if line.startswith("@@ -6386,6"):
        in_h8 = True
    if in_h8:
        if line.startswith("```") and not line.startswith("```diff"):
            break
        h8_lines.append(line)

print(f"H8 header: {h8_lines[0].strip()}")
print(f"H8 total diff lines: {len(h8_lines)}")

minus_lines = [l[1:] for l in h8_lines[1:] if l.startswith(" ") or l.startswith("-")]
plus_lines = [l[1:] for l in h8_lines[1:] if l.startswith(" ") or l.startswith("+")]

print(f"Minus lines count: {len(minus_lines)}")
print(f"Plus lines count: {len(plus_lines)}")

# 2. Check line 6386..6391 in mother_lines (1-based: 6386 is index 6385)
mother_h8 = mother_lines[6385:6385+len(minus_lines)]
print("Checking exact match with mother file:")
match = True
for idx, (m_line, d_line) in enumerate(zip(mother_h8, minus_lines), start=6386):
    if m_line != d_line:
        print(f"Mismatch at line {idx}:\n  Mother: {repr(m_line)}\n  Hunk -: {repr(d_line)}")
        match = False
    else:
        print(f"Match at line {idx}: {repr(m_line)}")

if match:
    print("ALL MINUS LINES EXACTLY MATCH MOTHER FILE!")
else:
    print("MISMATCH FOUND!")

# 3. Check position:
# mother line 6387 is: bak = backup_carrier(rec, carrier_dir)
# H8 insertion is right after line 6388 (budget.end_stage("backup"))
# launch is at line 6456
print(f"Mother line 6387: {repr(mother_lines[6386])}")
print(f"Mother line 6388: {repr(mother_lines[6387])}")
print(f"Insertion point is between mother line 6388 and line 6389: {repr(mother_lines[6388])}")

# 4. Check variables and symbols used in + lines:
# _pre_freshness_snapshot = make_pre_freshness_snapshot(carrier_dir / "except.txt")
# rec.add(FRESHNESS_GROUP, "captured_at_iso_pre", _pre_freshness_snapshot["captured_at_iso"], ...)
# carrier_dir: defined at line 6323 (create_isolated_carrier) or line 6289 (args.carrier_dir)
# rec: defined as arg to run_trip_carrier (line 6284)
# FRESHNESS_GROUP: defined at H01
# make_pre_freshness_snapshot: defined at H03
