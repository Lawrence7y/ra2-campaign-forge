# -*- coding: utf-8 -*-
"""M75 apply_coverage: modify exactly 22 coverage.tsv rows (cols 4,5,6), byte-preserving elsewhere.
Group A (12): NAMED_PUSH_S18_B5(9) + NAMED_PUSH_S17_B1(3) -> evidence NAMED_PUSH_AUDIT17/VERDICT.md
Group B (10): NAMED_PUSH_S15_B1(10) -> evidence NAMED_PUSH_AUDIT18/VERDICT.md
Cols 1/2/3/7/8 untouched; data rows stay 18,498; 8 tab-separated cols.
"""
import csv, os, re, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
MERGE = os.path.join(ROOT, "MERGE_M75")

D_S18 = os.path.join(ROOT, "NAMED_PUSH_S18_B5", "delta.tsv")
D_S17 = os.path.join(ROOT, "NAMED_PUSH_S17_B1", "delta.tsv")
D_S15 = os.path.join(ROOT, "NAMED_PUSH_S15_B1", "delta.tsv")
V_A = os.path.join(ROOT, "NAMED_PUSH_AUDIT17", "verdict.tsv")
V_B = os.path.join(ROOT, "NAMED_PUSH_AUDIT18", "verdict.tsv")

EV_A = "NAMED_PUSH_AUDIT17/VERDICT.md"
EV_B = "NAMED_PUSH_AUDIT18/VERDICT.md"
EXP_A = ["007B13D0", "007B1BC0", "007B2630", "007B26D0", "007B30B0",
         "007B31E0", "007B3450", "007B3890", "007B3AA0",
         "004A2CD0", "006BEF10", "006BF690"]
EXP_B = ["006E3E30", "006E57A0", "006E6470", "0071F930", "0071FA80",
         "00726860", "007268D0", "00726950", "00727BF0", "00727C80"]


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


def deltas(path):
    rows = read_tsv(path)
    assert rows[0][:6] == ["entry", "subsystem", "name", "one_line_semantics", "grade", "evidence_path"]
    return {ne(r[0]): r for r in rows[1:] if r}


def verdicts(path):
    rows = read_tsv(path)
    assert rows[0][:3] == ["entry", "subsystem", "verdict"]
    vv = {ne(r[0]): r for r in rows[1:] if r}
    assert all(r[2].strip() == "PASS" for r in rows[1:] if r), "not all PASS"
    return vv

d18, d17, d15 = deltas(D_S18), deltas(D_S17), deltas(D_S15)
dall = {}
for dd in (d18, d17, d15):
    for e, r in dd.items():
        dall[e] = r
vA, vB = verdicts(V_A), verdicts(V_B)

groupA = set(d18) | set(d17)
groupB = set(d15)
interA = groupA & set(vA)
interB = groupB & set(vB)
assert len(interA) == 12 and interA == set(EXP_A), ("A", len(interA), sorted(interA))
assert len(interB) == 10 and interB == set(EXP_B), ("B", len(interB), sorted(interB))
assert len(groupA & groupB) == 0
assert all(dall[e][4].strip() == "[已证]" for e in groupA | groupB)
assert all("[未证]" not in dall[e][3] for e in groupA | groupB)
print("PASS gates: A=12 B=10, all PASS, all [已证], all col4 free of literal [未证]")

# load coverage raw (LF, no trailing newline)
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

# sem/ev per entry
sem_ev = {}
for e in groupA:
    sem_ev[e] = (d18[e][3] if e in d18 else d17[e][3], EV_A)
for e in groupB:
    sem_ev[e] = (d15[e][3], EV_B)
assert len(sem_ev) == 22

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
assert len(changed) == 22, len(changed)
assert set(e for e, _, _, _ in changed) == set(EXP_A) | set(EXP_B)
for e, ln, old, new in changed:
    assert old[0] == new[0] and old[1] == new[1] and old[2] == new[2], (e, "cols1-3 changed")
    assert old[6] == new[6] and old[7] == new[7], (e, "cols7-8 changed")
    assert old[4].strip() != "[已证]", (e, "already proved")
    src = (d18[e] if e in d18 else d17[e]) if e in groupA else d15[e]
    assert new[3] == src[3], (e, "col4 not delta verbatim")
    assert new[4] == "[已证]", (e, "col5 wrong")
    assert new[5] == (EV_A if e in groupA else EV_B), (e, "col6 wrong")
    assert "[未证]" not in new[3], (e, "col4 has literal [未证]")
    print("  line %d %s grp=%s old_grade=%s -> [已证] ev=%s" %
          (ln, e, "A" if e in groupA else "B", old[4], new[5]))

out = "\n".join(lines)
with open(COV, "wb") as f:
    f.write(out.encode("utf-8"))

print("AFTER data rows:", len(lines) - 1)
print("AFTER bytes:", os.path.getsize(COV))
print("AFTER sha256:", hashlib.sha256(open(COV, "rb").read()).hexdigest())
