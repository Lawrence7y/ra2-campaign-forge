# -*- coding: utf-8 -*-
"""M76 apply_coverage: modify exactly 7 coverage.tsv rows (cols 4,5,6), byte-preserving elsewhere.
Group A (7): NAMED_PUSH_S06_B2(3) + NAMED_PUSH_S01S03_B1(1) + NAMED_PUSH_S16S21_B1(3)
  -> evidence NAMED_PUSH_AUDIT19/VERDICT.md
Cols 1/2/3/7/8 untouched; data rows stay 18,498; 8 tab-separated cols.
TWO word changes applied to col4:
  (1) 0071B1B0 slot addr 0071B1A0 -> 007F51A0
  (2) 0071CDA0 'ff 51 10 读入' -> 'ff 51 10 成员容器 slot4 下标查询（非读入）'
"""
import csv, os, re, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
MERGE = os.path.join(ROOT, "MERGE_M76")

D_S06 = os.path.join(ROOT, "NAMED_PUSH_S06_B2", "delta.tsv")
D_S0103 = os.path.join(ROOT, "NAMED_PUSH_S01S03_B1", "delta.tsv")
D_S1621 = os.path.join(ROOT, "NAMED_PUSH_S16S21_B1", "delta.tsv")
V_A = os.path.join(ROOT, "NAMED_PUSH_AUDIT19", "verdict.tsv")

EV = "NAMED_PUSH_AUDIT19/VERDICT.md"
EXP = ["005FEAF0", "006B5850", "0071CDA0", "00432050", "0046D000", "0046D090", "0071B1B0"]


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

d06, d0103, d1621 = deltas(D_S06), deltas(D_S0103), deltas(D_S1621)
dall = {}
for dd in (d06, d0103, d1621):
    for e, r in dd.items():
        dall[e] = r
vA = verdicts(V_A)
inter = set(dall) & set(vA)
assert len(inter) == 7 and inter == set(EXP), ("A", len(inter), sorted(inter))
assert all(dall[e][4].strip() == "[已证]" for e in inter)
assert all("[未证]" not in dall[e][3] for e in inter)
print("PASS gates: A=7, all PASS, all [已证], all col4 free of literal [未证]")

# ---- col4 semantic construction: delta verbatim + two mandated word changes ----
def col4_for(entry):
    s = dall[entry][3]
    if entry == "0071B1B0":
        # word change (1): slot address 0071B1A0 -> 007F51A0
        s2 = s.replace("0071B1A0", "007F51A0")
        print(f"  WORDCHANGE 0071B1B0: replaced 0071B1A0 -> 007F51A0 (occurrences in source: {s.count('0071B1A0')})")
        s = s2
    if entry == "0071CDA0":
        # word change (2): 'ff 51 10 读入' -> 'ff 51 10 成员容器 slot4 下标查询（非读入）'
        old = "ff 51 10 读入"
        new = "ff 51 10 成员容器 slot4 下标查询（非读入）"
        assert s.count(old) == 1, ("cda0 phrase count", s.count(old))
        s = s.replace(old, new, 1)
        print(f"  WORDCHANGE 0071CDA0: '{old}' -> '{new}'")
    return s

sem_ev = {e: (col4_for(e), EV) for e in inter}
assert len(sem_ev) == 7

# post-change assertions on the two rows
assert "007F51A0" in sem_ev["0071B1B0"][0] and "0071B1A0" not in sem_ev["0071B1B0"][0]
assert "成员容器 slot4 下标查询（非读入）" in sem_ev["0071CDA0"][0] and "ff 51 10 读入" not in sem_ev["0071CDA0"][0]
for e, (s, _) in sem_ev.items():
    assert "[未证]" not in s, (e, "col4 has literal [未证]")
print("PASS word-change assertions")

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

changed = []
for i in range(1, len(lines)):
    parts = lines[i].split("\t")
    if len(parts) != 8:
        continue
    e = ne(parts[0])
    if e in sem_ev:
        old = list(parts)
        parts[3] = sem_ev[e][0]   # col4 <- delta verbatim + mandated word changes
        parts[4] = "[已证]"       # col5
        parts[5] = sem_ev[e][1]   # col6
        assert len(parts) == 8
        lines[i] = "\t".join(parts)
        changed.append((e, i + 1, old, list(parts)))

print("changed rows:", len(changed))
assert len(changed) == 7, len(changed)
assert set(e for e, _, _, _ in changed) == set(EXP)
for e, ln, old, new in changed:
    assert old[0] == new[0] and old[1] == new[1] and old[2] == new[2], (e, "cols1-3 changed")
    assert old[6] == new[6] and old[7] == new[7], (e, "cols7-8 changed")
    assert old[4].strip() != "[已证]", (e, "already proved")
    assert new[4] == "[已证]", (e, "col5 wrong")
    assert new[5] == EV, (e, "col6 wrong")
    assert "[未证]" not in new[3], (e, "col4 has literal [未证]")
    extra = ""
    if e == "0071B1B0":
        extra = " | 007F51A0 in col4=%s, 0071B1A0 in col4=%s" % ("007F51A0" in new[3], "0071B1A0" in new[3])
    if e == "0071CDA0":
        extra = " | slot4 phrase in col4=%s, 'ff 51 10 读入' in col4=%s" % (
            "成员容器 slot4 下标查询（非读入）" in new[3], "ff 51 10 读入" in new[3])
    print("  line %d %s old_grade=%s -> [已证] ev=%s%s" % (ln, e, old[4], new[5], extra))

out = "\n".join(lines)
with open(COV, "wb") as f:
    f.write(out.encode("utf-8"))

print("AFTER data rows:", len(lines) - 1)
print("AFTER bytes:", os.path.getsize(COV))
print("AFTER sha256:", hashlib.sha256(open(COV, "rb").read()).hexdigest())
