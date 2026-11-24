# -*- coding: utf-8 -*-
"""Verify PANEL.md diff: only intended lines changed; 21 subsystem rows + TOTAL unchanged."""
import hashlib, re

BAK = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\PANEL.M52.bak"
NEW = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\PANEL.md"

def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

print("backup sha:", sha(BAK))
print("new    sha:", sha(NEW))
with open(BAK, "rb") as f: b = f.read()
with open(NEW, "rb") as f: n = f.read()
print("backup bytes:", len(b), "new bytes:", len(n))

bl = b.decode("utf-8").split("\n")
nl = n.decode("utf-8").split("\n")
print("backup lines(split):", len(bl), "new lines(split):", len(nl))

# Panel subsystem rows: lines starting "| Sxx |"
def panel_rows(lines):
    out = {}
    for l in lines:
        m = re.match(r'^\| (S\d\d) \| (\d[\d,]*) \| (\d+) \| ([\d.]+) \| (\d+) \| ([\d.]+) \| (\d+) \| ([\d.]+) \| (\d+) \| ([\d.]+) \|', l)
        if m:
            out[m.group(1)] = m.groups()[1:]
        if l.startswith("| **TOTAL** |") and "TOTAL" not in out:
            out["TOTAL"] = l  # only the main panel table's TOTAL row
    return out

br = panel_rows(bl)
nr = panel_rows(nl)
print("\n=== 21 subsystem rows + TOTAL diff ===")
changed = 0
for s in [f"S{i:02d}" for i in range(1,22)] + ["S22", "TOTAL"]:
    same = br.get(s) == nr.get(s)
    if not same:
        changed += 1
        print(f"  {s}: CHANGED")
        print(f"    old: {br.get(s)}")
        print(f"    new: {nr.get(s)}")
    else:
        print(f"  {s}: unchanged")
print("changed rows among S01-S21 + S22 + TOTAL:", changed)

# Which line numbers changed - use difflib
import difflib
sm = difflib.SequenceMatcher(a=bl, b=nl)
print("\n=== diff hunks (line-level) ===")
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        continue
    print(f"{tag}: old[{i1}:{i2}] -> new[{j1}:{j2}]")
    for l in bl[i1:i2]:
        print("  OLD:", l[:160])
    for l in nl[j1:j2]:
        print("  NEW:", l[:160])
