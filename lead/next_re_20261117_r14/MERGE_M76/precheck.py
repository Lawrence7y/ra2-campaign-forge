# -*- coding: utf-8 -*-
"""M76 precheck: record BEFORE mtime/bytes/sha256, verify all card preconditions.
NO writes to coverage.tsv / PANEL.md. Only writes MERGE_M76/_before.json.
"""
import csv, os, re, sys, hashlib, json, math, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
MERGE = os.path.join(ROOT, "MERGE_M76")

D_S06 = os.path.join(ROOT, "NAMED_PUSH_S06_B2", "delta.tsv")
D_S0103 = os.path.join(ROOT, "NAMED_PUSH_S01S03_B1", "delta.tsv")
D_S1621 = os.path.join(ROOT, "NAMED_PUSH_S16S21_B1", "delta.tsv")
V_A = os.path.join(ROOT, "NAMED_PUSH_AUDIT19", "verdict.tsv")

EXP = ["005FEAF0", "006B5850", "0071CDA0", "00432050", "0046D000", "0046D090", "0071B1B0"]
EV = "NAMED_PUSH_AUDIT19/VERDICT.md"


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

# ---------- BEFORE record (first, before any write) ----------
before = {"coverage.tsv": stat3(COV), "PANEL.md": stat3(PANEL)}
with open(os.path.join(MERGE, "_before.json"), "w", encoding="utf-8") as f:
    json.dump({k: list(v) for k, v in before.items()}, f, ensure_ascii=False, indent=2)
print("BEFORE coverage.tsv:", before["coverage.tsv"])
print("BEFORE PANEL.md     :", before["PANEL.md"])

# ---------- delta files ----------
def load_delta(path, want_n, tag):
    rows = read_tsv(path)
    assert rows[0][:6] == ["entry", "subsystem", "name", "one_line_semantics", "grade", "evidence_path"], (path, rows[0][:6])
    body = [r for r in rows[1:] if r]
    ck(f"{tag} delta row count == {want_n}", len(body), want_n)
    for r in body:
        ck(f"{tag} {r[0]} 6 cols", len(r) == 6, True)
        ck(f"{tag} {r[0]} entry 8-upper-hex", bool(re.fullmatch(r"[0-9A-F]{8}", r[0].strip())), True)
        ck(f"{tag} {r[0]} grade [已证]", r[4].strip(), "[已证]")
        ck(f"{tag} {r[0]} col4 free of literal [未证]", "[未证]" in r[3], False)
    return {ne(r[0]): r for r in body}

d06 = load_delta(D_S06, 3, "S06_B2")
d0103 = load_delta(D_S0103, 1, "S01S03_B1")
d1621 = load_delta(D_S1621, 3, "S16S21_B1")
all_delta = {}
for dd in (d06, d0103, d1621):
    for e, r in dd.items():
        ck(f"{e} not duplicated across delta files", e in all_delta, False)
        all_delta[e] = r
ck("7 distinct delta entries", len(all_delta), 7)
ck("delta set == EXP", sorted(all_delta), sorted(EXP))

# ---------- verdict ----------
vr = read_tsv(V_A)
assert vr[0][:3] == ["entry", "subsystem", "verdict"], vr[0][:3]
vbody = [r for r in vr[1:] if r]
vv = {ne(r[0]): r for r in vbody}
ck("AUDIT19 all verdict PASS", all(r[2].strip() == "PASS" for r in vbody), True)
ck("AUDIT19 verdict rows == 7", len(vbody), 7)

# ---------- INTERSECTION (HARD GATE) ----------
inter = set(all_delta) & set(vv)
ck("GROUP A intersection == 7", len(inter), 7)
ck("GROUP A intersection set == EXP", sorted(inter), sorted(EXP))
print(f">>> INTERSECTION A = {len(inter)} (need 7)")

# B group: confirm NO independent audit table (no NAMED_PUSH_AUDIT20)
audit20 = [d for d in os.listdir(ROOT) if d.startswith("NAMED_PUSH_AUDIT") and d.endswith("20")]
ck("no NAMED_PUSH_AUDIT20 (B group unaudited)", len(audit20), 0)

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
    text = f.read().decode("utf-8")
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
ck("full [已证] == 1643", full, 1643)
ck("atlas-in [已证] == 1637", atl_in, 1637)
ck("atlas-out [已证] == 6", atl_out, 6)
print(f">>> DISK full={full} atlas_in={atl_in} atlas_out={atl_out}")

# per-subsystem baseline
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
for s, wp, ws in (("S03", 38, 36), ("S06", 135, 120), ("S16", 47, 21), ("S21", 28, 28)):
    ck(f"BEFORE atlas-in proved {s} == {wp}", d[s]["proved"], wp)
    ck(f"BEFORE atlas-in strict {s} == {ws}", d[s]["strict"], ws)
    print(f">>> BEFORE {s}: atlas_n={d[s]['atlas_n']} named_S14={d[s]['named_S14']} proved={d[s]['proved']} strict={d[s]['strict']}")

def dod(key, dd):
    out = []
    for s in sorted(k for k in dd if re.match(r"^S\d\d$", k)):
        a = dd[s]["atlas_n"]; tn = math.ceil(0.9*a); tp = math.ceil(0.5*a)
        if dd[s]["named_S14"] >= tn and dd[s][key] >= tp:
            out.append(s)
    return out
n_before, s_before = dod("proved", d), dod("strict", d)
ck("BEFORE nominal 达标 set == S15,S16,S17", ",".join(n_before), "S15,S16,S17")
ck("BEFORE strict 达标 set == S17", ",".join(s_before), "S17")
print(">>> BEFORE DoD nominal=%s strict=%s" % (",".join(n_before), ",".join(s_before)))

# ---------- 7 rows membership/state ----------
by_entry = collections.defaultdict(list)
for i, r in enumerate(rows):
    by_entry[ne(r[0])].append((i + 2, r))
for e in EXP:
    hits = by_entry.get(e, [])
    ck(f"{e} appears exactly once in coverage", len(hits), 1)
    ck(f"{e} atlas-in", e in atlas, True)
    if len(hits) == 1:
        ln, r = hits[0]
        ck(f"{e} current grade not [已证]", r[4].strip() != "[已证]", True)
        print(f"  {e} line={ln} atlas_in={e in atlas} old_grade={r[4].strip()} sub={r[1].strip()} name={r[2].strip()}")

# projected counts
proj_full = full + len(EXP)  # all 7 atlas-in
proj_atl = atl_in + len([e for e in EXP if e in atlas])
ck("PROJECTED full [已证] == 1650", proj_full, 1650)
ck("PROJECTED atlas-in [已证] == 1644", proj_atl, 1644)
print(f">>> PROJECTED full={proj_full} atlas_in={proj_atl}")

# two word changes — verify SOURCE state explicitly
c_b1b0 = d1621["0071B1B0"][3]
c_cda0 = d06["0071CDA0"][3]
print(">>> WORDCHANGE SOURCE 0071B1B0: '0071B1A0' in col4?", "0071B1A0" in c_b1b0,
      "| '007F51A0' in col4?", "007F51A0" in c_b1b0)
print(">>> WORDCHANGE SOURCE 0071CDA0: 'ff 51 10 读入' in col4?", "ff 51 10 读入" in c_cda0)

# projected DoD (all new col4 free of literal [未证] => strict += proved)
def dod_projected():
    dd = {s: dict(c) for s, c in d.items()}
    adds = {"S03": 1, "S06": 3, "S16": 1, "S21": 2}
    for s, a in adds.items():
        dd[s]["proved"] += a
        dd[s]["strict"] += a
    return dod("proved", dd), dod("strict", dd), dd
n_after, s_after, dd_after = dod_projected()
ck("AFTER nominal 达标 set == S15,S16,S17 (no flip)", ",".join(n_after), "S15,S16,S17")
ck("AFTER strict 达标 set == S17 (no flip)", ",".join(s_after), "S17")
print(">>> AFTER DoD nominal=%s strict=%s" % (",".join(n_after), ",".join(s_after)))

# summary
npass = sum(1 for c in checks if c[0])
print("\n" + "=" * 70)
for ok, name, got, want in checks:
    if not ok:
        print("FAIL " + name + f"  got={got!r} want={want!r}")
print(f"CHECKS: {npass}/{len(checks)} pass")
print(f"GATE: A={len(inter)} B=0(unaudited) | full={full} atl_in={atl_in} atl_out={atl_out} | "
      f"flip_nominal={n_before!=n_after} flip_strict={s_before!=s_after}")
sys.exit(0 if npass == len(checks) else 1)
