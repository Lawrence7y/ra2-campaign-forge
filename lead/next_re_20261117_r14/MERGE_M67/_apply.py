# -*- coding: utf-8 -*-
"""M67 apply: 13 rows x 3 cols in coverage.tsv, with 0062FE90 table-address correction."""
import csv, os, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
D20 = os.path.join(ROOT, "NAMED_PUSH_S20_B2", "delta.tsv")
D06 = os.path.join(ROOT, "NAMED_PUSH_S06_B3", "delta.tsv")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
BAK = os.path.join(ROOT, "MERGE_M67", "coverage.tsv.bak")
EVID = "NAMED_PUSH_AUDIT7/VERDICT.md"

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

def sha256b(b):
    return hashlib.sha256(b).hexdigest().upper()

def read_tsv_rows(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f, delimiter="\t"))

# delta semantics map (col 4, index 3)
dmap = {}
for p in (D20, D06):
    for r in read_tsv_rows(p)[1:]:
        if len(r) >= 6 and r[0].strip():
            dmap[ne(r[0])] = r[3]

TARGETS = ['0062D9A0','0062FE90','00630090','00644960','006457A0','00645950',
           '0071E1D0','007220A0','007220D0','007281A0',
           '00749F30','0074BA30','00763D90']
TARGETS = [ne(x) for x in TARGETS]
assert len(TARGETS) == 13 and len(set(TARGETS)) == 13

# correction for 0062FE90: table address 007E9D84 -> 007E9D64 (both notations)
def fix_sem(sem, entry):
    if entry == ne("0062FE90"):
        assert sem.count("007E9D84") == 1, sem.count("007E9D84")
        assert sem.count("0x7E9D84") == 1, sem.count("0x7E9D84")
        sem = sem.replace("0x7E9D84", "0x7E9D64").replace("007E9D84", "007E9D64")
        assert "007E9D84" not in sem and "0x7E9D84" not in sem
        assert "007E9D64" in sem and "0x7E9D64" in sem
    return sem

for e in TARGETS:
    assert e in dmap, "delta missing %s" % e

raw = open(COV, "rb").read()
print("BEFORE sha=", sha256b(raw), "bytes=", len(raw))
open(BAK, "wb").write(raw)

text = raw.decode("utf-8")
lines = text.split("\n")
# 18,498 LF only, no trailing newline -> 18,499 elements: header + 18,498 data, last is data
assert len(lines) == 18499, len(lines)
assert lines[-1] != "" and "\t" in lines[-1], repr(lines[-1][:50])

# index target rows
hits = {e: [] for e in TARGETS}
for i in range(1, len(lines)):  # data lines: indices 1..18498 (18,498 rows)
    parts = lines[i].split("\t")
    if len(parts) != 8:
        continue
    e = ne(parts[0])
    if e in hits:
        hits[e].append(i)

for e in TARGETS:
    assert len(hits[e]) == 1, (e, len(hits[e]))
    i = hits[e][0]
    parts = lines[i].split("\t")
    assert len(parts) == 8
    assert parts[4].strip() == "[静态推断]", (e, parts[4])  # precondition: none already proved
    # save immutable cols
    old1, old2, old3, old7, old8 = parts[0], parts[1], parts[2], parts[6], parts[7]
    new4 = fix_sem(dmap[e], e)
    parts[3] = new4
    parts[4] = "[已证]"
    parts[5] = EVID
    # assert immutable cols unchanged
    assert parts[0]==old1 and parts[1]==old2 and parts[2]==old3 and parts[6]==old7 and parts[7]==old8
    lines[i] = "\t".join(parts)

new_text = "\n".join(lines)
new_raw = new_text.encode("utf-8")
open(COV, "wb").write(new_raw)
print("AFTER  sha=", sha256b(new_raw), "bytes=", len(new_raw))
print("changed rows=", len(TARGETS))
