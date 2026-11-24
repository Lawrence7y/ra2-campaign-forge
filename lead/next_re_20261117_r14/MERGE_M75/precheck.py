# -*- coding: utf-8 -*-
"""M75 precheck: record BEFORE mtime/bytes/sha256, verify all card preconditions + intersections.
NO writes to coverage.tsv / PANEL.md. Only writes MERGE_M75/_before.json.
"""
import csv, os, re, sys, hashlib, json, datetime, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
MERGE = os.path.join(ROOT, "MERGE_M75")

D_S18 = os.path.join(ROOT, "NAMED_PUSH_S18_B5", "delta.tsv")
D_S17 = os.path.join(ROOT, "NAMED_PUSH_S17_B1", "delta.tsv")
D_S15 = os.path.join(ROOT, "NAMED_PUSH_S15_B1", "delta.tsv")
V_A = os.path.join(ROOT, "NAMED_PUSH_AUDIT17", "verdict.tsv")
V_B = os.path.join(ROOT, "NAMED_PUSH_AUDIT18", "verdict.tsv")

EXP_A = ["007B13D0", "007B1BC0", "007B2630", "007B26D0", "007B30B0",
         "007B31E0", "007B3450", "007B3890", "007B3AA0",
         "004A2CD0", "006BEF10", "006BF690"]
EXP_B = ["006E3E30", "006E57A0", "006E6470", "0071F930", "0071FA80",
         "00726860", "007268D0", "00726950", "00727BF0", "00727C80"]
EXP_ALL = EXP_A + EXP_B


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


def stat3(path):
    st = os.stat(path)
    return (st.st_mtime, os.path.getsize(path),
            hashlib.sha256(open(path, "rb").read()).hexdigest())


checks = []
def ck(name, got, want):
    ok = (got == want)
    checks.append((ok, name, got, want))
    return ok

# ---------- BEFORE record (do this first, before any write) ----------
before = {"coverage.tsv": stat3(COV), "PANEL.md": stat3(PANEL)}
with open(os.path.join(MERGE, "_before.json"), "w", encoding="utf-8") as f:
    json.dump({k: list(v) for k, v in before.items()}, f, ensure_ascii=False, indent=2)
print("BEFORE coverage.tsv:", before["coverage.tsv"])
print("BEFORE PANEL.md     :", before["PANEL.md"])

# ---------- delta files ----------
def load_delta(path, want_n, want_sub, tag):
    rows = read_tsv(path)
    assert rows[0][:6] == ["entry", "subsystem", "name", "one_line_semantics", "grade", "evidence_path"], (path, rows[0][:6])
    body = [r for r in rows[1:] if r]
    ck(f"{tag} delta row count == {want_n}", len(body), want_n)
    for r in body:
        ck(f"{tag} {r[0]} 6 cols", len(r) == 6, True)
        ck(f"{tag} {r[0]} entry 8-upper-hex no 0x", bool(re.fullmatch(r"[0-9A-F]{8}", r[0].strip())), True)
        ck(f"{tag} {r[0]} grade [已证]", r[4].strip(), "[已证]")
        ck(f"{tag} {r[0]} subsystem {want_sub}", r[1].strip(), want_sub)
        ck(f"{tag} {r[0]} col4 free of literal [未证]", "[未证]" in r[3], False)
    return {ne(r[0]): r for r in body}

d18 = load_delta(D_S18, 9, "S18", "S18_B5")
d17 = load_delta(D_S17, 3, "S17", "S17_B1")
d15 = load_delta(D_S15, 10, "S15", "S15_B1")

all_delta = {}
for dd in (d18, d17, d15):
    for e, r in dd.items():
        ck(f"{e} not duplicated across delta files", e in all_delta, False)
        all_delta[e] = r
ck("22 distinct delta entries", len(all_delta), 22)
ck("delta set == EXP_ALL", sorted(all_delta), sorted(EXP_ALL))

# ---------- verdict files ----------
def load_verdict(path, tag):
    rows = read_tsv(path)
    assert rows[0][:3] == ["entry", "subsystem", "verdict"], (path, rows[0][:3])
    body = [r for r in rows[1:] if r]
    vv = {ne(r[0]): r for r in body}
    ck(f"{tag} all verdict PASS", all(r[2].strip() == "PASS" for r in body), True)
    return vv

vA = load_verdict(V_A, "AUDIT17")
vB = load_verdict(V_B, "AUDIT18")
print("verdict A rows:", len(vA), "verdict B rows:", len(vB))

# ---------- INTERSECTIONS (the hard gate) ----------
set_A_delta = set(d18) | set(d17)
set_B_delta = set(d15)
interA = set_A_delta & set(vA)
interB = set_B_delta & set(vB)
ck("GROUP A intersection == 12", len(interA), 12)
ck("GROUP B intersection == 10", len(interB), 10)
ck("GROUP A intersection set == EXP_A", sorted(interA), sorted(EXP_A))
ck("GROUP B intersection set == EXP_B", sorted(interB), sorted(EXP_B))
ck("A and B intersections disjoint", len(interA & interB), 0)
ck("total intersection == 22", len(interA | interB), 22)
print(f">>> INTERSECTION A = {len(interA)}  B = {len(interB)}  (need 12 + 10)")

# ---------- atlas ----------
atlas = set()
with open(ATLAS, encoding="utf-8-sig", newline="") as f:
    rd = csv.reader(f, delimiter="\t"); next(rd)
    for r in rd:
        if r and r[0].strip():
            atlas.add(ne(r[0]))
print("atlas entries:", len(atlas))

# ---------- coverage current state ----------
with open(COV, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8")
ck("coverage no BOM", text.startswith("\ufeff"), False)
ck("coverage no CR", "\r" in text, False)
lines = text.split("\n")
data = lines[1:]
ck("coverage data rows == 18498", len(data), 18498)
ck("all data rows exactly 8 cols", sum(1 for ln in data if len(ln.split("\t")) != 8), 0)
ck("coverage no trailing newline", lines[-1] == "", False)

rows = [ln.split("\t") for ln in data]
full = sum(1 for r in rows if r[4].strip() == "[已证]")
atl_in = sum(1 for r in rows if ne(r[0]) in atlas and r[4].strip() == "[已证]")
atl_out = full - atl_in
ck("full [已证] == 1621", full, 1621)
ck("atlas-in [已证] == 1615", atl_in, 1615)
ck("atlas-out [已证] == 6", atl_out, 6)
print(f">>> DISK full={full} atlas_in={atl_in} atlas_out={atl_out}")

# per-subsystem proved/strict baseline (authoritative strict_panel.py line 78)
RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")
RE_SLOT = re.compile(r"::v?slot\d+$")
d = collections.defaultdict(collections.Counter)
for r in rows:
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

for s, want in (("S18", 57), ("S15", 106), ("S17", 56)):
    ck(f"BEFORE atlas-in proved {s} == {want}", d[s]["proved"], want)
print(">>> BEFORE proved S18=%d S15=%d S17=%d" % (d["S18"]["proved"], d["S15"]["proved"], d["S17"]["proved"]))

# DoD baseline
import math
def dod_set(key):
    out = []
    for s in sorted(k for k in d if re.match(r"^S\d\d$", k)):
        a = d[s]["atlas_n"]; tn = math.ceil(0.9*a); tp = math.ceil(0.5*a)
        if d[s]["named_S14"] >= tn and d[s][key] >= tp:
            out.append(s)
    return out
n_before, s_before = dod_set("proved"), dod_set("strict")
ck("BEFORE nominal 达标 set == S15,S16,S17", ",".join(n_before), "S15,S16,S17")
ck("BEFORE strict 达标 set == S17", ",".join(s_before), "S17")
print(">>> BEFORE DoD nominal=%s strict=%s" % (",".join(n_before), ",".join(s_before)))

# ---------- 22 rows: atlas membership, coverage presence, current state ----------
by_entry = collections.defaultdict(list)
for i, r in enumerate(rows):
    by_entry[ne(r[0])].append((i + 2, r))  # 1-based physical line = i+2 (header is line 1)

for e in EXP_ALL:
    hits = by_entry.get(e, [])
    ck(f"{e} appears exactly once in coverage", len(hits), 1)
    ck(f"{e} atlas-in", e in atlas, True)
    if len(hits) == 1:
        ln, r = hits[0]
        ck(f"{e} current grade not [已证]", r[4].strip() != "[已证]", True)
        print(f"  {e} line={ln} atlas_in={e in atlas} old_grade={r[4].strip()} sub={r[1].strip()} name={r[2].strip()}")

# Projected after counts
proj_full = full + len([e for e in EXP_ALL])
proj_atl = atl_in + len([e for e in EXP_ALL if e in atlas])
ck("PROJECTED full [已证] == 1643", proj_full, 1643)
ck("PROJECTED atlas-in [已证] == 1637", proj_atl, 1637)
print(f">>> PROJECTED full={proj_full} atlas_in={proj_atl} atlas_out={proj_full-proj_atl}")

# Projected per-subsystem proved / strict (all new semantics free of [未证] => strict += proved)
for s, add, want_p, want_st in (("S18", 9, 66, None), ("S15", 10, 116, None), ("S17", 3, 59, None)):
    ck(f"PROJECTED {s} proved == {want_p}", d[s]["proved"] + add, want_p)

# Projected DoD (named unchanged; proved rises; strict rises by same add since col4 has no [未证])
def dod_projected():
    dd = {s: dict(c) for s, c in d.items()}
    adds = {"S18": 9, "S15": 10, "S17": 3}
    for s, a in adds.items():
        dd[s]["proved"] += a
        dd[s]["strict"] += a
    out = []
    for s in sorted(k for k in dd if re.match(r"^S\d\d$", k)):
        a = dd[s]["atlas_n"]; tn = math.ceil(0.9*a); tp = math.ceil(0.5*a)
        if dd[s]["named_S14"] >= tn and dd[s]["proved"] >= tp:
            out.append(s)
    strout = []
    for s in sorted(k for k in dd if re.match(r"^S\d\d$", k)):
        a = dd[s]["atlas_n"]; tn = math.ceil(0.9*a); tp = math.ceil(0.5*a)
        if dd[s]["named_S14"] >= tn and dd[s]["strict"] >= tp:
            strout.append(s)
    return out, strout, dd

n_after, s_after, dd_after = dod_projected()
ck("AFTER nominal 达标 set == S15,S16,S17 (no flip)", ",".join(n_after), "S15,S16,S17")
ck("AFTER strict 达标 set == S17 (no flip)", ",".join(s_after), "S17")
print(">>> AFTER DoD nominal=%s strict=%s" % (",".join(n_after), ",".join(s_after)))
for s in ("S18", "S15", "S17"):
    print(">>> PROJECTED %s proved=%d strict=%d atlas_n=%d named_S14=%d" %
          (s, dd_after[s]["proved"], dd_after[s]["strict"], dd_after[s]["atlas_n"], dd_after[s]["named_S14"]))
print(">>> TOTAL atlas-in proved=%d strict=%d" %
      (sum(c["proved"] for c in dd_after.values()), sum(c["strict"] for c in dd_after.values())))

# ---------- summary ----------
npass = sum(1 for c in checks if c[0])
print("\n" + "=" * 70)
for ok, name, got, want in checks:
    if not ok:
        print("FAIL " + name + f"  got={got!r} want={want!r}")
print(f"CHECKS: {npass}/{len(checks)} pass")
print(f"GATE: A={len(interA)} B={len(interB)} | full={full} atl_in={atl_in} atl_out={atl_out} | "
      f"S18={d['S18']['proved']} S15={d['S15']['proved']} S17={d['S17']['proved']} | "
      f"flip_nominal={n_before!=n_after} flip_strict={s_before!=s_after}")
sys.exit(0 if npass == len(checks) else 1)
