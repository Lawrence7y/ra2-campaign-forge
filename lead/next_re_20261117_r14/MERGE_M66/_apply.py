# -*- coding: utf-8 -*-
"""Apply M66 coverage.tsv edits: 29 rows x cols 4/5/6. Byte-precise line-based edit."""
import csv, os, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
MERGE = os.path.join(ROOT, "MERGE_M66")
BAK = os.path.join(MERGE, "coverage.tsv.bak")

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def load_delta(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    return {r[0].strip(): r for r in rows[1:] if r and r[0].strip()}

def pass_set(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))[1:]
    return set(r[0].strip() for r in rows if r[2].strip() == "PASS")

p6 = pass_set(os.path.join(ROOT, "NAMED_PUSH_AUDIT6", "verdict.tsv"))
with open(os.path.join(ROOT, "NAMED_PUSH_AUDIT5", "verdict.tsv"), encoding="utf-8-sig", newline="") as f:
    p5rows = list(csv.reader(f, delimiter="\t"))[1:]
p5_06 = set(r[0].strip() for r in p5rows if r[2].strip()=="PASS" and r[1].strip()=="S06")
p5_20 = set(r[0].strip() for r in p5rows if r[2].strip()=="PASS" and r[1].strip()=="S20")

dd22 = load_delta(os.path.join(ROOT, "NAMED_PUSH_S22_B2", "delta.tsv"))
dd06 = load_delta(os.path.join(ROOT, "NAMED_PUSH_S06_B1", "delta.tsv"))
dd20 = load_delta(os.path.join(ROOT, "NAMED_PUSH_S20_B1", "delta.tsv"))

# Build target map: entry -> (delta_row, evidence_path, group)
targets = {}
for e in sorted(p6 & set(dd22)):
    targets[e] = (dd22[e], "NAMED_PUSH_AUDIT6/VERDICT.md", "A/S22")
for e in sorted(p5_06 & set(dd06)):
    targets[e] = (dd06[e], "NAMED_PUSH_AUDIT5/VERDICT.md", "B/S06")
for e in sorted(p5_20 & set(dd20)):
    targets[e] = (dd20[e], "NAMED_PUSH_AUDIT5/VERDICT.md", "B/S20")
assert len(targets) == 29, len(targets)

# Read raw bytes -> text (utf-8, no BOM, LF)
with open(COV, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8")
lines = text.split("\n")
# lines[0] = header; lines[1:] = data (last element may be '' if trailing newline)
assert lines[0].startswith("entry,subsystem,name,one_line_semantics,grade,evidence_path")
# Determine data line indices
data_idxs = [i for i in range(1, len(lines)) if lines[i] != ""]
assert len(data_idxs) == 18498, len(data_idxs)

# Build entry -> line index map (first column)
entry_line = {}
for i in data_idxs:
    e = lines[i].split("\t")[0].strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        e = "%08X" % int(e, 16)
    except ValueError:
        pass
    if e in entry_line:
        raise SystemExit(f"duplicate normalized entry in coverage: {e}")
    entry_line[e] = i

# Apply edits
changed = 0
for e, (dr, evid, grp) in targets.items():
    ne = e.strip().upper()
    if ne.startswith("0X"):
        ne = ne[2:]
    try:
        ne = "%08X" % int(ne, 16)
    except ValueError:
        pass
    if ne not in entry_line:
        raise SystemExit(f"target entry not found in coverage: {e}")
    i = entry_line[ne]
    cols = lines[i].split("\t")
    if len(cols) != 8:
        raise SystemExit(f"target row not 8 cols: {e} -> {len(cols)}")
    # only 3 columns change
    cols[3] = dr[3]
    cols[4] = "[已证]"
    cols[5] = evid
    lines[i] = "\t".join(cols)
    changed += 1
assert changed == 29, changed

new_text = "\n".join(lines)
new_raw = new_text.encode("utf-8")
# Safety backup (before overwrite)
with open(BAK, "wb") as f:
    f.write(raw)
# Write new content atomically-ish (same dir)
tmp = COV + ".tmp66"
with open(tmp, "wb") as f:
    f.write(new_raw)
os.replace(tmp, COV)

print("sha before:", sha256(BAK))
print("sha after :", sha256(COV))
print("bytes before:", len(raw), "bytes after:", len(new_raw))
print("changed rows:", changed)
