# -*- coding: utf-8 -*-
import hashlib
from pathlib import Path

design_path = Path(r"D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\B2B_DESIGN.md")
mother_path = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py")

mother_bytes = mother_path.read_bytes()
mother_sha = hashlib.sha256(mother_bytes).hexdigest()
print(f"Mother sha: {mother_sha}, len: {len(mother_bytes)}")
assert mother_sha == "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636"

mother_lines = mother_path.read_text(encoding="utf-8").splitlines(keepends=True)

text = design_path.read_text(encoding="utf-8")
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

print(f"Total hunks found: {len(hunks)}")
h6 = hunks[5]
print("H6 header:", h6[0].strip())
for l in h6:
    print("  ", repr(l))

# Verify - lines against mother
old_lines = []
new_lines = []
for l in h6[1:]:
    if l.startswith(" "):
        old_lines.append(l[1:])
        new_lines.append(l[1:])
    elif l.startswith("-"):
        old_lines.append(l[1:])
    elif l.startswith("+"):
        new_lines.append(l[1:])

start_idx = 5936 - 1  # 0-based
slice_from_mother = mother_lines[start_idx : start_idx + len(old_lines)]

print("Match check:")
print(f"len(old_lines) = {len(old_lines)}, len(slice_from_mother) = {len(slice_from_mother)}")
match = (old_lines == slice_from_mother)
print(f"Exact match: {match}")
if not match:
    for i, (o, m) in enumerate(zip(old_lines, slice_from_mother)):
        if o != m:
            print(f"Diff at line {i}: old={repr(o)} vs mother={repr(m)}")
else:
    print("All - lines and context match mother lines 5936..5942 exactly!")

# Check H7 and H8 as well:
h7 = hunks[6]
print("\nH7 header:", h7[0].strip())
h8 = hunks[7]
print("H8 header:", h8[0].strip())
