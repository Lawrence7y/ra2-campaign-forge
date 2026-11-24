# -*- coding: utf-8 -*-
"""M72 apply: modify exactly 11 coverage.tsv rows (cols 4,5,6), byte-preserving elsewhere.
Group A: NAMED_PUSH_AUDIT13/verdict.tsv ∩ NAMED_PUSH_S07_B1/delta.tsv  -> 7 rows (S07)
Group B: NAMED_PUSH_AUDIT14/verdict.tsv ∩ NAMED_PUSH_S11_B1/delta.tsv  -> 4 rows (S11)
S09_B1's single row is explicitly NOT merged.
"""
import csv, os, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
FA  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"

A_VERDICT = os.path.join(ROOT, "NAMED_PUSH_AUDIT13", "verdict.tsv")
A_DELTA   = os.path.join(ROOT, "NAMED_PUSH_S07_B1", "delta.tsv")
B_VERDICT = os.path.join(ROOT, "NAMED_PUSH_AUDIT14", "verdict.tsv")
B_DELTA   = os.path.join(ROOT, "NAMED_PUSH_S11_B1", "delta.tsv")
S09_DELTA = os.path.join(ROOT, "NAMED_PUSH_S09_B1", "delta.tsv")

EV_A = "NAMED_PUSH_AUDIT13/VERDICT.md"
EV_B = "NAMED_PUSH_AUDIT14/VERDICT.md"

EXPECT_A = ["00421730","004370C0","00491210","005550C0","00555110","00555150","006DBD20"]
EXPECT_B = ["004AF720","004B62C0","004B6470","0054DC60"]

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

def read_tsv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.reader(f, delimiter="\t")]

# verdict: entry -> (subsystem, verdict)
def verdicts(path):
    rows = read_tsv(path)
    assert rows[0][:3] == ["entry","subsystem","verdict"], (path, rows[0][:3])
    return {ne(r[0]): (r[1], r[2].strip()) for r in rows[1:] if r}

# delta: entry -> (subsystem, semantics col4)
def deltas(path):
    rows = read_tsv(path)
    assert rows[0][:6] == ["entry","subsystem","name","one_line_semantics","grade","evidence_path"], (path, rows[0][:6])
    return {ne(r[0]): (r[1], r[3]) for r in rows[1:] if r}

av, bv = verdicts(A_VERDICT), verdicts(B_VERDICT)
ad, bd = deltas(A_DELTA), deltas(B_DELTA)
s09 = deltas(S09_DELTA)

print("A verdict rows=%d delta rows=%d" % (len(av), len(ad)))
print("B verdict rows=%d delta rows=%d" % (len(bv), len(bd)))
print("S09 delta rows=%d entries=%s" % (len(s09), sorted(s09)))

# ---- HARD GATES: parallel counts must be exactly 7 and 4 ----
interA = set(av) & set(ad)
interB = set(bv) & set(bd)
assert len(av) == 7 and len(ad) == 7, ("A row counts", len(av), len(ad))
assert len(bv) == 4 and len(bd) == 4, ("B row counts", len(bv), len(bd))
assert len(interA) == 7, ("A intersection", interA)
assert len(interB) == 4, ("B intersection", interB)
assert sorted(interA) == sorted(ne(x) for x in EXPECT_A), ("A entries", sorted(interA))
assert sorted(interB) == sorted(ne(x) for x in EXPECT_B), ("B entries", sorted(interB))
assert all(av[e][0] == "S07" and av[e][1] == "PASS" for e in interA), "A verdict not S07/PASS"
assert all(bv[e][0] == "S11" and bv[e][1] == "PASS" for e in interB), "B verdict not S11/PASS"
assert not (interA & interB), "groups overlap"
assert not (set(s09) & (interA | interB)), "S09 row leaked into merge"
print("PASS parallel counts 7+4; intersections exact; all PASS; S09 excluded")

# ---- atlas membership (lowercase normalized) ----
atlas = set()
with open(FA, encoding="utf-8") as f:
    rd = csv.reader(f, delimiter="\t"); next(rd)
    for r in rd:
        if r and r[0].strip():
            atlas.add(r[0].strip().lower())
assert len(atlas) == 12916, len(atlas)
targets = interA | interB
for e in targets:
    assert e.lower() in atlas, ("not in atlas", e)
print("PASS all 11 target entries atlas-in (atlas data rows 12,916)")

# ---- load coverage raw ----
with open(COV, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8")
lines = text.split("\n")
data = lines[1:]
assert len(data) == 18498, ("data rows", len(data))
assert all(len(ln.split("\t")) == 8 for ln in data), "non-8-col data row"

sem_ev = {}
for e in interA:
    sem_ev[e] = (ad[e][1], EV_A)
for e in interB:
    sem_ev[e] = (bd[e][1], EV_B)

changed = []
for i in range(1, len(lines)):
    parts = lines[i].split("\t")
    if len(parts) != 8:
        continue
    e = ne(parts[0])
    if e in sem_ev:
        old = list(parts)
        parts[3] = sem_ev[e][0]   # col4 <- delta original
        parts[4] = "[已证]"       # col5
        parts[5] = sem_ev[e][1]   # col6
        assert len(parts) == 8
        lines[i] = "\t".join(parts)
        changed.append((e, i + 1, old, list(parts)))

print("changed rows:", len(changed))
assert len(changed) == 11, len(changed)
assert set(e for e, _, _, _ in changed) == targets
for e, ln, old, new in changed:
    assert old[0] == new[0] and old[1] == new[1] and old[2] == new[2], (e, "cols1-3 changed")
    assert old[6] == new[6] and old[7] == new[7], (e, "cols7-8 changed")
    assert old[4] != "[已证]", (e, "already proved")
    print("  line %d %s col4/5/6 updated (cols 1/2/3/7/8 intact)" % (ln, e))

out = "\n".join(lines)
with open(COV, "wb") as f:
    f.write(out.encode("utf-8"))

print("AFTER bytes:", os.path.getsize(COV))
print("AFTER sha256:", hashlib.sha256(open(COV, "rb").read()).hexdigest())
