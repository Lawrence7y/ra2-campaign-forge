# -*- coding: utf-8 -*-
"""M60 Part 1: merge 34 rows' col4 semantics + col6 evidence_path. Grade untouched."""
import os, re, json, hashlib

BASE = "D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14"
COV = os.path.join(BASE, "COVERAGE", "coverage.tsv")
DELTA = [
    (os.path.join(BASE, "SEMFIX_ENGFAM_B1", "coverage_delta.tsv"), "SEMFIX_ENGFAM_B1/_audit/VERDICT.md"),
    (os.path.join(BASE, "SEMFIX_ENGFAM_B2", "coverage_delta.tsv"), "SEMFIX_ENGFAM_B2/_audit/VERDICT.md"),
]

def read_lines(p):
    b = open(p, "rb").read()
    assert b[:3] != b"\xef\xbb\xbf"
    s = b.decode("utf-8")
    # normalize all line-ending styles to logical lines (delta files are CRLF)
    return s.splitlines(), s.endswith(("\n", "\r"))

delta = {}
for path, ev in DELTA:
    lines, _ = read_lines(path)
    hdr = lines[0].split("\t")
    assert hdr == ["entry", "subsystem", "name", "one_line_semantics", "grade", "evidence_path"], hdr
    for ln in lines[1:]:
        f = ln.split("\t")
        assert len(f) == 6
        e = f[0].strip().upper()
        assert re.fullmatch(r"[0-9A-F]{8}", e)
        assert e not in delta, "dup delta entry %s" % e
        delta[e] = (f[3], ev)
assert len(delta) == 34

cov_lines, trailing = read_lines(COV)
assert cov_lines[0] == "entry,subsystem,name,one_line_semantics,grade,evidence_path,n_sources,conflict"
changed = []
new_lines = [cov_lines[0]]
for i, ln in enumerate(cov_lines[1:], 2):
    f = ln.split("\t")
    assert len(f) == 8, (i, len(f))
    e = f[0].strip().upper()
    if e in delta:
        sem, ev = delta[e]
        assert f[4] == "[已证]", "grade not [已证] for %s: %r" % (e, f[4])
        f[3] = sem
        f[5] = ev
        changed.append(e)
    new_lines.append("\t".join(f))

assert len(changed) == 34 and len(set(changed)) == 34
assert set(changed) == set(delta)
out = "\n".join(new_lines) + ("\n" if trailing else "")
with open(COV, "wb") as fh:
    fh.write(out.encode("utf-8"))

lines2, trailing2 = read_lines(COV)
assert len(lines2) == len(cov_lines)
assert trailing2 == trailing
for i, (a, b) in enumerate(zip(cov_lines, lines2), 1):
    if i == 1:
        assert a == b; continue
    fa, fb = a.split("\t"), b.split("\t")
    e = fa[0].strip().upper()
    if e in delta:
        for idx in (0, 1, 2, 4, 6, 7):
            assert fa[idx] == fb[idx], "col%d changed for %s" % (idx+1, e)
        assert fb[3] == delta[e][0], "col4 not verbatim for %s" % e
        assert fb[5] == delta[e][1], "col6 wrong for %s" % e
    else:
        assert a == b, "unexpected change at line %d" % i
print("MERGED %d rows; bytes after=%d" % (len(changed), len(out.encode("utf-8"))))
print("sha256 after=", hashlib.sha256(out.encode("utf-8")).hexdigest().upper())
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "merged_entries.json"), "w", encoding="utf-8") as fh:
    json.dump({"changed": changed}, fh, ensure_ascii=False, indent=2)
print("WROTE merged_entries.json")
