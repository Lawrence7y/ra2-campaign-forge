# -*- coding: utf-8 -*-
"""R16-D1-WIDE-B2 independent verification (read-only everything)."""
import io, os, sys, re, json, hashlib, collections, bisect

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
PROBE = os.path.join(R14, "R16_PROBE_4FINAL")
ROOT = os.path.dirname(os.path.dirname(R14))
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
SIEVE = os.path.join(R14, "R16_SIEVE_D1_WIDE", "sieve_all.tsv")
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
sys.path.insert(0, PROBE)
import final as F

def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()
def readtsv(p):
    L = io.open(p, encoding="utf-8-sig").read().splitlines()
    h = L[0].split("\t"); out = []
    for ln in L[1:]:
        c = ln.rstrip("\r\n").split("\t")
        if len(c) >= len(h): out.append(dict(zip(h, c)))
    return out

res = {}
# --- entry set derivation
sv = readtsv(SIEVE)
no = sorted([r for r in sv if r["has_ring4_on_disk(是/否)"] == "否"], key=lambda x: int(x["entry"], 16))
b1 = set(r["entry"] for r in no[:18])
b2 = set(r["entry"] for r in no[18:36])
res["n_no_ring4"] = len(no)
res["b1_b2_overlap"] = len(b1 & b2)
# --- delta
dl = io.open(os.path.join(HERE, "delta.tsv"), encoding="utf-8").read().splitlines()
hdr = dl[0].split("\t")
cov = {}
for ln in io.open(COV, encoding="utf-8-sig").read().splitlines()[1:]:
    c = ln.rstrip("\r\n").split("\t")
    if len(c) >= 8:
        cov[c[0].strip().upper()] = c
checks = dict(n_rows=len(dl)-1, col4_prefix=True, cols_exact=True,
              has_disc=True, has_s126=True, has_required_fields=True,
              entry_set_ok=True, col3_grade_ok=True)
seen = set()
dentries = []
for ln in dl[1:]:
    c = ln.split("\t")
    assert len(c) == 8, "delta not 8 cols"
    e = c[0].upper(); dentries.append(e)
    cr = cov[e]
    # cols 1/2/3/5/6/7/8 byte-identical
    for i in (0,1,2,4,5,6,7):
        if c[i] != cr[i]:
            checks["cols_exact"] = False
    if not (c[3].startswith(cr[3]) and len(c[3]) > len(cr[3])):
        checks["col4_prefix"] = False
    newer = c[3][len(cr[3]):]
    if "（D-47(A) 裁决" not in newer or "§12.6" not in newer:
        checks["has_disc"] = False; checks["has_s126"] = False
    for tok in ("④ 活表槽位见证：", "（vt=", "，槽 ", " 值=", "，COL=", " offset=",
                "，RTTI=", "；装表点 ", " 位于 ", " 体内，", "装配方式=", "实测指令 ", "entry 体外）", "④升级句："):
        if tok not in newer:
            checks["has_required_fields"] = False
    if "④" in cr[3]:
        checks["col4_prefix"] = False  # pre already had ④
    seen.add(newer)
res["delta_checks"] = checks
res["delta_entry_set_equals_b2"] = (set(dentries) == b2 and len(dentries) == 18)
res["delta_unique_col4"] = len(seen) == len(dl)-1

# --- normalize-entry uniqueness
norm = set(re.sub(r"[0-9A-Fa-f]{8}", "ENTRY", x) for x in seen)
res["norm_unique"] = len(norm) == len(dl)-1

# --- fields cross-check vs raw_dump
flds = readtsv(os.path.join(HERE, "fields.tsv"))
fmap = {r["entry"]: r for r in flds}
dump = json.load(io.open(os.path.join(HERE, "raw_dump.json"), encoding="utf-8"))
rmap = {x["entry"]: x for x in dump["recs"]}
fv = dict(n=len(flds), vt_match=True, slot_match=True, site_match=True,
          status_match=True, install_form_in_enum=True)
VALID_FORM = {"ctor_body", "mov_abs", "reg", "other"}
for r in flds:
    e = r["entry"]; x = rmap.get(e, {})
    if r["vt"] != x.get("vt"): fv["vt_match"] = False
    if r["slot"] != str(x.get("slot")): fv["slot_match"] = False
    if r["install_site"] != x.get("site"): fv["site_match"] = False
    if r["install_form(ctor_body|mov_abs|reg|other)"] not in VALID_FORM: fv["install_form_in_enum"] = False
    exp = "CLASS_FIX" if x.get("class_fix") else "OK"
    if r["status(OK|SKIP-ALREADY|SKIP|CLASS_FIX)"] != exp: fv["status_match"] = False
res["fields_checks"] = fv

# --- independent 6-point byte check on gamemd.exe (read-only, via final.Image)
img = F.Image(EXE)
atlas = F.load_atlas()
all6 = True
per = []
for e in sorted(b2):
    x = rmap[e]
    vt = int(x["vt"], 16); slot = int(x["slot"]); ei = int(e, 16)
    col = img.u32(vt - 4)
    coff = img.u32(col + 4) if col else None
    td = img.u32(col + 12) if col else None
    mg = img.cstr(td + 8) if td else None
    sv2 = img.u32(vt + slot * 4)
    site = int(x["site"], 16)
    sz = atlas.get(ei, 0)
    ok6 = [
        sv2 == ei,
        col is not None and img.u32(col) == 0,
        coff == 0,
        td is not None and (mg or "").startswith(".?A"),
        not (ei <= site < ei + sz),
        vt is not None,
    ]
    if not all(ok6): all6 = False
    per.append(dict(entry=e, ok6=all(ok6), chk=ok6))
res["independent_all6"] = all6
res["independent_failed_rows"] = [p["entry"] for p in per if not p["ok6"]]

# --- hashes
res["cov_sha"] = sha(COV); res["cov_bytes"] = os.path.getsize(COV)
res["exe_sha"] = sha(EXE)
res["cov_sha_unchanged"] = res["cov_sha"] == "412ED7E36BC1AD4907763FEBB3A68D5FDABB3F0D2C999800444B57098B1AB2E1"
res["exe_sha_expected"] = res["exe_sha"] == "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"

io.open(os.path.join(HERE, "verify_independent.json"), "w", encoding="utf-8").write(
    json.dumps(res, ensure_ascii=False, indent=1))
print(json.dumps(res, ensure_ascii=False, indent=1))
