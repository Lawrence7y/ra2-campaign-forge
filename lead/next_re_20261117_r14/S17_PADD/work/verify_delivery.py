"""Verify S17_PADD delivery: delta format, forbidden words, post-merge metrics."""
import re

TAB = chr(9)
BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COV = BASE + r"\COVERAGE\coverage.tsv"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
DELTA = BASE + r"\S17_PADD\coverage_delta.tsv"

atlas = set()
for ln in open(ATLAS, encoding="utf-8", errors="replace").read().splitlines()[1:]:
    c = ln.split(TAB)
    if c: atlas.add(c[0].upper())

cov = {}
for ln in open(COV, encoding="utf-8", errors="replace").read().splitlines()[1:]:
    c = ln.split(TAB)
    if len(c) >= 5: cov[c[0].upper()] = c

# parse delta
dlines = open(DELTA, encoding="utf-8").read().splitlines()
hdr = dlines[0].split(TAB)
print("delta header cols:", hdr)
assert hdr == ["entry","subsystem","name","one_line_semantics","grade","evidence_path"]
delta = []
for ln in dlines[1:]:
    c = ln.split(TAB)
    assert len(c) == 6, ("col count", len(c), ln[:80])
    assert c[1] == "S17"
    assert c[0].upper() in atlas, ("not in atlas", c[0])
    delta.append(c)
print("delta rows:", len(delta))
for c in delta:
    print("  ", c[0], c[2], c[4], "| evidence", c[5])
    bad = [w for w in ("未证","未定","弱信号","线索") if w in c[3]]
    assert not bad, ("forbidden word", c[0], bad)
print("forbidden-word check: PASS")

# post-merge metrics
def named_S(name):
    return name != "" and not name.startswith("sub_") and not re.search(r"::sub_[0-9A-Fa-f]+$", name)

def metrics(rows):
    n = len(rows)
    ns = sum(1 for r in rows if named_S(r[2]))
    proved = sum(1 for r in rows if r[4] == "[已证]")
    strict = sum(1 for r in rows if r[4] == "[已证]" and "[未证]" not in r[3])
    return n, ns, proved, strict

s17 = [c for c in cov.values() if c[1] == "S17" and c[0].upper() in atlas]
n0,ns0,p0,s0 = metrics(s17)
print("BASELINE n/named_S/proved/strict:", n0, ns0, p0, s0)
print("  thresholds named=%d proved=%d strict=%d" % (
    -(-9*n0//10), -(-5*n0//10), -(-5*n0//10)))

# apply delta
post = {k: list(v) for k,v in cov.items()}
for c in delta:
    post[c[0].upper()] = c
s17p = [r for r in post.values() if r[1] == "S17" and r[0].upper() in atlas]
n1,ns1,p1,s1 = metrics(s17p)
print("POST n/named_S/proved/strict:", n1, ns1, p1, s1)
print("  margins: named=%+d proved=%+d strict=%+d" % (
    ns1 - (-(-9*n1//10)), p1 - (-(-5*n1//10)), s1 - (-(-5*n1//10))))
