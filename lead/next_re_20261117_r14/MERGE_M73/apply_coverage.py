# -*- coding: utf-8 -*-
"""M73 apply: modify exactly 2 coverage.tsv rows (cols 4,5,6), byte-preserving elsewhere.
007B10C0 (S18) from NAMED_PUSH_S18_B4/delta.tsv
004F45B0 (S09) from NAMED_PUSH_S09_B1/delta.tsv
Both PASS in NAMED_PUSH_AUDIT15/verdict.tsv -> evidence NAMED_PUSH_AUDIT15/VERDICT.md
"""
import csv, os, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
FA  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
VERDICT = os.path.join(ROOT, "NAMED_PUSH_AUDIT15", "verdict.tsv")
DELTA_S18 = os.path.join(ROOT, "NAMED_PUSH_S18_B4", "delta.tsv")
DELTA_S09 = os.path.join(ROOT, "NAMED_PUSH_S09_B1", "delta.tsv")

EV = "NAMED_PUSH_AUDIT15/VERDICT.md"
EXPECT = {"007B10C0": "S18", "004F45B0": "S09"}


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


def verdicts(path):
    rows = read_tsv(path)
    assert rows[0][:3] == ["entry", "subsystem", "verdict"], (path, rows[0][:3])
    return {ne(r[0]): (r[1].strip(), r[2].strip()) for r in rows[1:] if r}


def deltas(path):
    rows = read_tsv(path)
    assert rows[0][:6] == ["entry", "subsystem", "name", "one_line_semantics", "grade", "evidence_path"], (path, rows[0][:6])
    return {ne(r[0]): (r[1].strip(), r[2].strip(), r[3], r[4].strip(), r[5]) for r in rows[1:] if r}


v = verdicts(VERDICT)
d18 = deltas(DELTA_S18)
d09 = deltas(DELTA_S09)
print("verdict rows=%d, S18 delta rows=%d, S09 delta rows=%d" % (len(v), len(d18), len(d09)))

# ---- HARD GATES ----
assert len(v) == 2, ("verdict rows", len(v))
assert set(v) == set(EXPECT), ("verdict entries", sorted(v))
assert all(v[e][1] == "PASS" for e in v), "not all PASS"
assert all(v[e][0] == EXPECT[e] for e in EXPECT), "verdict subsystem mismatch"
assert len(d18) == 1 and len(d09) == 1, ("delta row counts", len(d18), len(d09))
assert set(d18) == {"007B10C0"}, sorted(d18)
assert set(d09) == {"004F45B0"}, sorted(d09)
print("PASS parallel count 2 (1 S18 + 1 S09); verdict 2/2 PASS; deltas exact")

# delta subsystem/name checks vs expectation
for e, sub in EXPECT.items():
    dd = d18 if e == "007B10C0" else d09
    assert dd[e][0] == sub, (e, "delta subsystem", dd[e][0])
print("PASS delta subsystems match")

# ---- atlas membership ----
atlas = set()
with open(FA, encoding="utf-8") as f:
    rd = csv.reader(f, delimiter="\t"); next(rd)
    for r in rd:
        if r and r[0].strip():
            atlas.add(ne(r[0]))
assert len(atlas) == 12916, len(atlas)
for e in EXPECT:
    assert e in atlas, ("not in atlas", e)
print("PASS both target entries atlas-in (atlas data rows 12,916)")

# ---- load coverage raw (LF, no trailing newline) ----
with open(COV, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8")
lines = text.split("\n")
data = lines[1:]
assert len(data) == 18498, ("data rows", len(data))
assert all(len(ln.split("\t")) == 8 for ln in data), "non-8-col data row"

sem_ev = {}
for e in EXPECT:
    dd = d18 if e == "007B10C0" else d09
    sem = dd[e][2]
    assert "[未证]" not in sem, (e, "delta semantics contains literal [未证]")
    sem_ev[e] = (sem, EV)

changed = []
for i in range(1, len(lines)):
    parts = lines[i].split("\t")
    if len(parts) != 8:
        continue
    e = ne(parts[0])
    if e in sem_ev:
        old = list(parts)
        parts[3] = sem_ev[e][0]   # col4 <- delta original verbatim
        parts[4] = "[已证]"       # col5
        parts[5] = sem_ev[e][1]   # col6
        assert len(parts) == 8
        lines[i] = "\t".join(parts)
        changed.append((e, i + 1, old, list(parts)))

print("changed rows:", len(changed))
assert len(changed) == 2, len(changed)
assert set(e for e, _, _, _ in changed) == set(EXPECT)
for e, ln, old, new in changed:
    assert old[0] == new[0] and old[1] == new[1] and old[2] == new[2], (e, "cols1-3 changed")
    assert old[6] == new[6] and old[7] == new[7], (e, "cols7-8 changed")
    assert old[4].strip() != "[已证]", (e, "already proved")
    print("  line %d %s col4/5/6 updated (cols 1/2/3/7/8 intact, old grade=%s)" % (ln, e, old[4]))

out = "\n".join(lines)
with open(COV, "wb") as f:
    f.write(out.encode("utf-8"))

print("AFTER bytes:", os.path.getsize(COV))
print("AFTER sha256:", hashlib.sha256(open(COV, "rb").read()).hexdigest())
