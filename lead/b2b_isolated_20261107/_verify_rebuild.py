# -*- coding: utf-8 -*-
"""_verify_rebuild.py — 独立（自写 hunk 应用器）复核 母本+CANDIDATE_LF.diff == 隔离副本，逐字节。只读。"""
import os
import re
import hashlib

ROOT = r"D:/Project/ra2-campaign-forge"
MOTHER = os.path.join(ROOT, "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py")
ISOL = os.path.join(ROOT, "lead/b2b_isolated_20261107/qc151_trip.isolated.py")
CANDDIFF = os.path.join(ROOT, "lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff")

mb = open(MOTHER, "rb").read()
ib = open(ISOL, "rb").read()
diff_txt = open(CANDDIFF, "rb").read().decode("utf-8")
m_lines = mb.decode("utf-8").split("\n")
d_lines = diff_txt.split("\n")

# split into hunk bodies at @@ headers
first = next(i for i, l in enumerate(d_lines) if l.startswith("@@ "))
bodies, cur = [], None
for l in d_lines[first:]:
    if l.startswith("@@ "):
        if cur is not None:
            bodies.append(cur)
        cur = [l]
    elif cur is not None:
        cur.append(l)
if cur is not None:
    bodies.append(cur)
bodies = [b for b in bodies if any(x.startswith("@@ ") for x in b)]
print("hunk bodies =", len(bodies))

out = list(m_lines)
offset = 0
for bi, body in enumerate(bodies, 1):
    while body and body[-1] == "":
        body.pop()
    hdr = body[0]
    g = re.match(r"@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@", hdr)
    old_start = int(g.group(1))
    old_count = int(g.group(2) or 1)
    new_count = int(g.group(4) or 1)
    mi = old_start - 1
    consumed = 0
    produced = []
    for l in body[1:]:
        tag, rest = (l[0], l[1:]) if l else (" ", "")
        if tag == " ":
            assert m_lines[mi + consumed] == rest, f"hunk{bi} context mismatch at mother line {mi+consumed+1}"
            produced.append(m_lines[mi + consumed]); consumed += 1
        elif tag == "-":
            assert m_lines[mi + consumed] == rest, f"hunk{bi} minus mismatch at mother line {mi+consumed+1}"
            consumed += 1
        elif tag == "+":
            produced.append(rest)
        else:
            raise AssertionError(f"hunk{bi} bad line {l[:30]!r}")
    assert consumed == old_count, f"hunk{bi} consumed {consumed} != {old_count}"
    assert len(produced) == new_count, f"hunk{bi} produced {len(produced)} != {new_count}"
    op = old_start - 1 + offset
    out[op:op + consumed] = produced
    offset += len(produced) - consumed

rebuilt = "\n".join(out).encode("utf-8")
print("rebuilt sha256 =", hashlib.sha256(rebuilt).hexdigest(), "bytes =", len(rebuilt))
print("isolated sha256 =", hashlib.sha256(ib).hexdigest(), "bytes =", len(ib))
print("mother+CANDIDATE_LF.diff == isolated (byte-for-byte) =", rebuilt == ib)
print("also matches candidate expected ca23c116... =", hashlib.sha256(rebuilt).hexdigest() == "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2")
