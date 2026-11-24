# -*- coding: utf-8 -*-
"""M74 precheck: verify all card preconditions and the exact-6 intersection BEFORE any write."""
import csv, os, sys, hashlib, collections, re
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
VERDICT = os.path.join(ROOT, "NAMED_PUSH_AUDIT16", "verdict.tsv")
DELTA = os.path.join(ROOT, "NAMED_PUSH_S13_B1", "delta.tsv")

EXPECT = ["004684E0", "00629FD0", "0075E0C0", "0075E2C0", "00772CD0", "00772EB0"]
EV = "NAMED_PUSH_AUDIT16/VERDICT.md"


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


def stat(p):
    st = os.stat(p)
    return (st.st_mtime, os.path.getsize(p), hashlib.sha256(open(p, "rb").read()).hexdigest())


print("=" * 70)
print("M74 PRECHECK (before any write)")
print("=" * 70)

# ---- BEFORE stat of two files ----
print("\n-- BEFORE stat --")
for p in (COV, PANEL):
    m, b, h = stat(p)
    print(os.path.basename(p))
    print("  mtime  :", m)
    print("  bytes  :", b)
    print("  sha256 :", h)

# ---- atlas ----
atlas = set()
with open(ATLAS, encoding="utf-8-sig") as f:
    rd = csv.reader(f, delimiter="\t"); hdr = next(rd)
    for r in rd:
        if r and r[0].strip():
            atlas.add(ne(r[0]))
print("\n-- atlas --")
print("atlas data rows (unique normalized entries):", len(atlas))

# ---- verdict ----
vrows = read_tsv(VERDICT)
assert vrows[0][:3] == ["entry", "subsystem", "verdict"], vrows[0][:3]
verdict = {}
for r in vrows[1:]:
    if r:
        verdict[ne(r[0])] = (r[1].strip(), r[2].strip())
print("\n-- verdict.tsv --")
print("verdict rows:", len(verdict))
for e in sorted(verdict):
    print("  ", e, verdict[e])

# ---- delta ----
drows = read_tsv(DELTA)
assert drows[0][:6] == ["entry", "subsystem", "name", "one_line_semantics", "grade", "evidence_path"], drows[0][:6]
delta = {}
for r in drows[1:]:
    if r:
        delta[ne(r[0])] = (r[1].strip(), r[2].strip(), r[3], r[4].strip(), r[5])
print("\n-- delta.tsv --")
print("delta rows:", len(delta))
for e in sorted(delta):
    print("  ", e, "sub=", delta[e][0], "grade=", delta[e][3], "sem=[", delta[e][2][:50], "]")

# ---- intersection ----
inter = set(verdict) & set(delta)
print("\n-- intersection (verdict ∩ delta) --")
print("intersection count:", len(inter))
print("intersection entries:", sorted(inter))
print("expected entries   :", EXPECT)
assert len(inter) == 6, ("INTERSECTION NOT 6", len(inter), sorted(inter))
assert set(EXPECT) == inter, ("INTERSECTION MISMATCH", sorted(inter))
assert all(verdict[e][1] == "PASS" for e in inter), "NOT ALL PASS"
assert all(verdict[e][0] == "S13" for e in inter), "verdict subsystem not S13"
assert all(delta[e][0] == "S13" for e in inter), "delta subsystem not S13"
assert all(delta[e][3] == "[已证]" for e in inter), "delta grade not [已证]"
print("PASS intersection exactly 6, all S13, all verdict PASS")

# ---- delta col4 strict literal check ----
print("\n-- delta col4 [未证] literal check --")
for e in EXPECT:
    has = "[未证]" in delta[e][2]
    print("  ", e, "contains [未证]:", has)
    assert not has, (e, "delta semantics contains literal [未证]")
print("PASS no delta semantics contains literal [未证]")

# ---- coverage load ----
with open(COV, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8")
has_bom = raw.startswith(b"\xef\xbb\xbf")
crlf = text.count("\r\n")
lines = text.split("\n")
header = lines[0]
data = lines[1:]
print("\n-- coverage.tsv --")
print("BOM:", has_bom, "CRLF count:", crlf, "has \\r:", "\r" in text)
print("raw bytes:", len(raw), "text split lines:", len(lines))
print("header:", repr(header[:120]))
print("data rows (split by \\n):", len(data))
assert len(data) == 18498, ("data rows", len(data))
non8 = [i+2 for i, ln in enumerate(data) if len(ln.split("\t")) != 8]
print("non-8-col data rows:", len(non8))
assert not non8, ("non-8-col rows", non8[:10])

# trailing newline check
print("trailing newline (last line empty):", lines[-1] == "")

# ---- counts using csv parse ----
rows = read_tsv(COV)
hdr = rows[0]
datarows = [r for r in rows[1:] if len(r) >= 8]
full = sum(1 for r in datarows if r[4].strip() == "[已证]")
atl_in = sum(1 for r in datarows if ne(r[0]) in atlas and r[4].strip() == "[已证]")
atl_out = full - atl_in
print("\n-- counts (card preconditions) --")
print("data rows            :", len(datarows), "(want 18498)")
print("full [已证]          :", full, "(want 1615)")
print("atlas-in [已证]      :", atl_in, "(want 1609)")
print("atlas-out [已证]     :", atl_out, "(want 6)")
assert len(datarows) == 18498
assert full == 1615, ("full", full)
assert atl_in == 1609, ("atlas-in", atl_in)
assert atl_out == 6, ("atlas-out", atl_out)
print("PASS all table-level preconditions")

# ---- per-subsystem proved/strict/named (authoritative strict_panel.py line 78) ----
d = collections.defaultdict(collections.Counter)
RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")
RE_SLOT = re.compile(r"::v?slot\d+$")
for r in datarows:
    e = ne(r[0]); s = r[1].strip()
    if e not in atlas:
        continue
    name, sem, grade = r[2].strip(), r[3], r[4].strip()
    d[s]["atlas_n"] += 1
    if name and not name.startswith("sub_"):
        d[s]["named_L"] += 1
        if not RE_CSUB.search(name):
            d[s]["named_S14"] += 1
            if not RE_SLOT.search(name):
                d[s]["named_strict"] += 1
    if grade == "[已证]":
        d[s]["proved"] += 1
        if "[未证]" not in sem:
            d[s]["strict"] += 1

print("\n-- S13 counts (card precondition) --")
print("S13 atlas_n      :", d["S13"]["atlas_n"])
print("S13 proved       :", d["S13"]["proved"], "(want 100)")
print("S13 strict       :", d["S13"]["strict"])
print("S13 named_S14    :", d["S13"]["named_S14"])
assert d["S13"]["proved"] == 100, ("S13 proved", d["S13"]["proved"])
print("PASS S13 proved = 100")

# ---- target rows in coverage ----
print("\n-- target rows in coverage --")
for e in EXPECT:
    hits = [r for r in datarows if ne(r[0]) == e]
    print("  ", e, "hits=", len(hits))
    assert len(hits) == 1, (e, "coverage hits", len(hits))
    r = hits[0]
    print("      sub=", r[1], "name=", r[2])
    print("      col5(grade)=", r[4].strip(), "col6(ev)=", r[5].strip())
    print("      atlas-in=", ne(r[0]) in atlas)
print("PASS each of 6 entries appears exactly once in coverage")

# ---- 达标 sets (before) ----
import math
nominal, strict_ok = [], []
for s in sorted(k for k in d if re.match(r"^S\d\d$", k)):
    a = d[s]["atlas_n"]; tn = math.ceil(0.9*a); tp = math.ceil(0.5*a)
    if d[s]["named_S14"] >= tn and d[s]["proved"] >= tp:
        nominal.append(s)
    if d[s]["named_S14"] >= tn and d[s]["strict"] >= tp:
        strict_ok.append(s)
print("\n-- 达标 sets (before) --")
print("nominal:", ",".join(nominal))
print("strict :", ",".join(strict_ok))

print("\n" + "=" * 70)
print("PRECHECK ALL PASS — safe to proceed")
print("=" * 70)
