# -*- coding: utf-8 -*-
"""M71 apply: modify exactly the 11 coverage.tsv rows (cols 4,5,6), byte-preserving elsewhere."""
import csv, os, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
DELTA= os.path.join(ROOT, "NAMED_PUSH_S22_B4", "delta.tsv")
AUDIT= os.path.join(ROOT, "NAMED_PUSH_AUDIT12", "verdict.tsv")

EXPECT = ["006C5210","006C5390","006C5510","006C5690","006C5810",
          "006C5990","006C5B10","006C5C90","006C5E10","006C5F90","006C6110"]

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

# delta semantics + audit verdict by entry
sem = {}
with open(DELTA, encoding="utf-8-sig", newline="") as f:
    for r in list(csv.reader(f, delimiter="\t"))[1:]:
        if len(r) >= 4:
            sem[ne(r[0])] = r[3]
audit = {}
with open(AUDIT, encoding="utf-8-sig", newline="") as f:
    for r in list(csv.reader(f, delimiter="\t"))[1:]:
        if len(r) >= 3:
            audit[ne(r[0])] = r[2].strip()
inter = set(sem) & set(audit)
assert inter == set(EXPECT), ("intersection mismatch", inter)
assert all(audit[e] == "PASS" for e in inter), {e:audit[e] for e in inter}

with open(COV, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8")
lines = text.split("\n")
print("split line count:", len(lines), "last-empty:", lines[-1]=="")

changed = []
for i, line in enumerate(lines):
    if i == 0:
        continue
    parts = line.split("\t")
    if len(parts) != 8:
        continue
    e = ne(parts[0])
    if e in sem:
        old = list(parts)
        parts[3] = sem[e]                              # col 4 semantics <- delta original
        parts[4] = "[已证]"                            # col 5 grade
        parts[5] = "NAMED_PUSH_AUDIT12/VERDICT.md"     # col 6 evidence_path
        assert len(parts) == 8
        lines[i] = "\t".join(parts)
        changed.append((e, i, old, list(parts)))

print("changed rows:", len(changed))
assert len(changed) == 11, len(changed)
assert sorted(e for e,_,_,_ in changed) == sorted(EXPECT)
for e, i, old, new in changed:
    assert old[0] == new[0] and old[1] == new[1] and old[2] == new[2]
    assert old[6] == new[6] and old[7] == new[7], (e, old[6:8], new[6:8])
    print(f"  line {i+1}: {e} cols4/5/6 updated; cols1/2/3/7/8 intact")

out = "\n".join(lines)
with open(COV, "wb") as f:
    f.write(out.encode("utf-8"))

sha = hashlib.sha256(open(COV,"rb").read()).hexdigest()
print("AFTER bytes:", os.path.getsize(COV))
print("AFTER sha256:", sha)
