# -*- coding: utf-8 -*-
"""M74 apply_coverage: modify exactly 6 coverage.tsv rows (cols 4,5,6), byte-preserving elsewhere.
6 S13 rows from NAMED_PUSH_S13_B1/delta.tsv, all PASS in NAMED_PUSH_AUDIT16/verdict.tsv.
"""
import csv, os, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
VERDICT = os.path.join(ROOT, "NAMED_PUSH_AUDIT16", "verdict.tsv")
DELTA = os.path.join(ROOT, "NAMED_PUSH_S13_B1", "delta.tsv")

EV = "NAMED_PUSH_AUDIT16/VERDICT.md"
EXPECT = ["004684E0", "00629FD0", "0075E0C0", "0075E2C0", "00772CD0", "00772EB0"]


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
d = deltas(DELTA)
print("verdict rows=%d, delta rows=%d" % (len(v), len(d)))

# ---- HARD GATES ----
assert len(v) == 6, ("verdict rows", len(v))
assert len(d) == 6, ("delta rows", len(d))
assert set(v) == set(EXPECT), ("verdict entries", sorted(v))
assert set(d) == set(EXPECT), ("delta entries", sorted(d))
assert all(v[e][1] == "PASS" for e in v), "not all PASS"
assert all(v[e][0] == "S13" for e in v), "verdict subsystem mismatch"
assert all(d[e][0] == "S13" for e in d), "delta subsystem mismatch"
assert all(d[e][3] == "[已证]" for e in d), "delta grade not [已证]"
inter = set(v) & set(d)
assert len(inter) == 6, ("INTERSECTION NOT 6", len(inter))
assert inter == set(EXPECT), ("INTERSECTION MISMATCH", sorted(inter))
print("PASS intersection exactly 6; verdict 6/6 PASS; deltas exact; all S13")

for e in EXPECT:
    assert "[未证]" not in d[e][2], (e, "delta semantics contains literal [未证]")
print("PASS delta col4 all free of literal [未证]")

# ---- load coverage raw (LF, no trailing newline) ----
with open(COV, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8")
assert not text.startswith("\ufeff"), "unexpected BOM"
assert "\r" not in text, "unexpected CR"
lines = text.split("\n")
data = lines[1:]
assert len(data) == 18498, ("data rows", len(data))
assert all(len(ln.split("\t")) == 8 for ln in data), "non-8-col data row"
assert lines[-1] != "", "unexpected trailing newline"

sem_ev = {e: (d[e][2], EV) for e in EXPECT}

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
assert len(changed) == 6, len(changed)
assert set(e for e, _, _, _ in changed) == set(EXPECT)
for e, ln, old, new in changed:
    assert old[0] == new[0] and old[1] == new[1] and old[2] == new[2], (e, "cols1-3 changed")
    assert old[6] == new[6] and old[7] == new[7], (e, "cols7-8 changed")
    assert old[4].strip() != "[已证]", (e, "already proved")
    assert new[3] == d[e][2], (e, "col4 not delta verbatim")
    assert new[4] == "[已证]" and new[5] == EV, (e, "col5/6 wrong")
    print("  line %d %s col4/5/6 updated (cols 1/2/3/7/8 intact, old grade=%s)" % (ln, e, old[4]))

out = "\n".join(lines)
with open(COV, "wb") as f:
    f.write(out.encode("utf-8"))

print("AFTER data rows:", len(lines) - 1)
print("AFTER bytes:", os.path.getsize(COV))
print("AFTER sha256:", hashlib.sha256(open(COV, "rb").read()).hexdigest())
