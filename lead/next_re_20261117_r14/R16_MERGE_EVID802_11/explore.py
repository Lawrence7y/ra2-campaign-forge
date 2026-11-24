# -*- coding: utf-8 -*-
"""Read-only exploration: locate the 11 target rows, compare delta col6 vs current."""
import hashlib, os, sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
DELTA = os.path.join(ROOT, "R16_EVID802_11", "coverage_delta.tsv")

TARGETS = ["0045A560","0045A610","0053C6A0","005514B0","00551560","00557090",
           "00557140","006B1850","006B1900","006B8660","006B8710"]

def sha(b): return hashlib.sha256(b).hexdigest().upper()

def load_lines(path):
    with open(path, "rb") as f:
        raw = f.read()
    # LF-only file; last line may have no trailing newline
    parts = raw.split(b"\n")
    trailing_nl = raw.endswith(b"\n")
    if trailing_nl:
        parts = parts[:-1]
    return raw, parts, trailing_nl

cov_raw, cov_lines, cov_trail = load_lines(COV)
delta_raw, delta_lines, delta_trail = load_lines(DELTA)
print("COV raw bytes=%d sha=%s lines=%d trailing_nl=%s" % (len(cov_raw), sha(cov_raw), len(cov_lines), cov_trail))
print("DELTA raw bytes=%d sha=%s lines=%d trailing_nl=%s" % (len(delta_raw), sha(delta_raw), len(delta_lines), delta_trail))
# line-ending census on raw
crlf = cov_raw.count(b"\r\n"); lf = cov_raw.count(b"\n"); cr = cov_raw.count(b"\r")
print("COV line endings: LF=%d CRLF=%d loneCR=%d  (lf-crlf=%d)" % (lf, crlf, cr, lf-crlf))
print("COV header:", cov_lines[0].decode("utf-8"))

# delta header
d_header = delta_lines[0].decode("utf-8").split("\t")
print("DELTA header cols:", d_header)
delta_col6 = {}
for ln in delta_lines[1:]:
    if not ln.strip(): continue
    f = ln.decode("utf-8").split("\t")
    assert len(f)==8, ("delta bad col count", len(f))
    delta_col6[f[0]] = f[5]
print("DELTA entries:", list(delta_col6.keys()))
assert set(delta_col6) == set(TARGETS), "delta entries mismatch"

# find targets in coverage
cov_index = {}
for i, ln in enumerate(cov_lines[1:], start=2):
    f = ln.split(b"\t")
    e = f[0].decode("ascii").upper()
    if e in TARGETS:
        cov_index.setdefault(e, []).append((i, len(f), f))
print("\n--- coverage target rows ---")
for e in TARGETS:
    occ = cov_index.get(e, [])
    print("%s occurrences=%d lines=%s colcounts=%s" % (e, len(occ), [x[0] for x in occ], [x[1] for x in occ]))

print("\n--- per-target compare: current col6 vs delta col6 ---")
for e in TARGETS:
    occ = cov_index[e]
    assert len(occ)==1, (e, "not unique")
    lineno, ncol, fields = occ[0]
    assert ncol==8, (e, ncol)
    cur_col6 = fields[5].decode("utf-8")
    new_col6 = delta_col6[e]
    prefix_ok = new_col6.startswith(cur_col6 + ";")
    print("line %d %s" % (lineno, e))
    print("  CUR  col6 = %r" % cur_col6)
    print("  NEW  col6 = %r" % new_col6)
    print("  strict-prefix(cur+';') = %s" % prefix_ok)
    # other columns compare: delta row vs cov row
    drow = None
    for ln in delta_lines[1:]:
        f = ln.decode("utf-8").split("\t")
        if f[0]==e: drow=f; break
    crow = [x.decode("utf-8") for x in fields]
    diffs = [(j, crow[j][:40], drow[j][:40]) for j in range(8) if crow[j]!=drow[j]]
    print("  col diffs (idx,cur[:40],delta[:40]) = %s" % diffs)

# note uniqueness checks (Lead self-check re-verification)
notes = {}
for e in TARGETS:
    new_col6 = delta_col6[e]
    segs = new_col6.split(";")
    note = segs[-1]
    notes[e]=note
import re
def norm_entry(s): return re.sub(r"\b[0-9A-F]{8}\b", "<ENTRY>", s)
def norm_allhex(s): return re.sub(r"\b[0-9A-Fa-f]{8}\b", "<HEX8>", s)
print("\nnotes unique=%d  entry-normalized unique=%d  hex8-normalized unique=%d" % (
    len(set(notes.values())),
    len(set(norm_entry(v) for v in notes.values())),
    len(set(norm_allhex(v) for v in notes.values()))))

# path part byte-identical check: compare to _coverage_after.tsv in audit dir? skip; just report path segments
print("\n--- path segments (before ';M94') ---")
for e in TARGETS:
    new_col6 = delta_col6[e]
    idx = new_col6.find(";M94")
    print("%s path=%r" % (e, new_col6[:idx]))

# resolve PROOF paths on disk
print("\n--- PROOF path isfile/nonempty ---")
bases = [("r14", ROOT), ("lead", os.path.dirname(ROOT)), ("repo", r"D:\Project\ra2-campaign-forge")]
for e in TARGETS:
    new_col6 = delta_col6[e]
    segs = new_col6.split(";")
    proof = segs[1]  # e.g. S10_KPROVED\EVIDENCE\PROOF_0045A560.txt
    rel = proof.replace("\\", os.sep).split("#",1)[0]
    hit = None
    for bn, base in bases:
        p = os.path.join(base, rel)
        if os.path.isfile(p):
            hit = (bn, p, os.path.getsize(p)); break
    print("%s proof=%r hit=%s" % (e, proof, hit))
