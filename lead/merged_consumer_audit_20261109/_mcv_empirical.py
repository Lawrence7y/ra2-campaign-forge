# -*- coding: utf-8 -*-
# _mcv_empirical.py -- independent empirical check.
# 1) Load _re_linked.py READ-ONLY via importlib, produce a GENUINE merged rec from the
#    existing Ffull_merged fixture (no writes to any read-only file).
# 2) Feed that rec into the exact expressions found in downstream consumers, using
#    the consumer's own source text where possible (extracted by exec of a minimal copy).
# Prints stdout only; writes nothing. sys.dont_write_bytecode=True.
import sys
sys.dont_write_bytecode = True
import hashlib, importlib.util
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
RE = ROOT / "lead" / "r33e_merge_20261109" / "_re_linked.py"
FIX = ROOT / "lead" / "r33e_merge_20261109" / "_re_fixtures" / "Ffull_merged"

spec = importlib.util.spec_from_file_location("_mcv_re_linked", RE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

blob = (FIX / "a_one.py").read_bytes()
FH = hashlib.sha256(blob).hexdigest()
NB = len(blob)
text = (FIX / "doc.md").read_text(encoding="utf-8")
problems, warnings, rec = m.link_triple(text, FIX, FH, NB)

print("=== GENUINE MERGED REC ===")
print("link verdict      =", m.link(text, FIX, FH, NB)["verdict"])
print("tier              =", rec.get("tier"))
print("match             =", rec.get("match"))
print("path              =", rec.get("path"))
print("keys              =", sorted(rec.keys()))
for k in ("verified_path", "recomputed", "bytes"):
    print("has %-13s = %s" % (k, k in rec))
print("members_n         =", len(rec.get("members") or []))
print("decl_lines        =", rec.get("decl_lines"))
print("problems          =", problems)

TRIALS = []

def trial(name, fn):
    try:
        r = fn(rec)
        TRIALS.append((name, "OK", repr(r)))
        print("[%s] OK -> %r" % (name, r))
    except Exception as e:
        TRIALS.append((name, "CRASH", "%s: %s" % (type(e).__name__, e)))
        print("[%s] CRASH -> %s: %s" % (name, type(e).__name__, e))

# A. _f2v_verify9.py:21-29 (exact source lines, inverse guard + Path + bytes subscript)
def A(rec):
    b = rec
    if b.get("match") is not True:
        return "skipped"
    src = b.get("alt") or b
    vp = Path(src.get("verified_path") or src.get("path"))
    data = vp.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    size = len(data)
    ok_sha = sha == b["declared"].lower()
    ok_bytes = size == src["bytes"]
    return (ok_sha, ok_bytes)
trial("A _f2v_verify9.py:21-29", A)

# A2. same but only the Path() line
def A2(rec):
    src = rec.get("alt") or rec
    return Path(src.get("verified_path") or src.get("path"))
trial("A2 _f2v_verify9.py:24 Path(None)", A2)

# A3. only the bytes subscript
def A3(rec):
    src = rec.get("alt") or rec
    return src["bytes"]
trial("A3 _f2v_verify9.py:29 src['bytes']", A3)

# B. _f2w_checks.py:28-35  (unlisted by author)
def B(rec):
    b = rec
    if b.get("match") is not True:
        return "skipped"
    sha_ok = (b.get("recomputed") or "").lower() == b["declared"].lower()
    return sha_ok
trial("B _f2w_checks.py:28-29", B)

# C. _f2_selftest.py:110
def C(rec):
    return rec.get("verified_path", "").endswith("_f2_r11plus.py")
trial("C _f2_selftest.py:110", C)

# D. _f2_compare.py:66-69 counters
def D(rec):
    n_bind = [rec]
    return (sum(1 for b in n_bind if b.get("path")),
            sum(1 for b in n_bind if b.get("match") is True))
trial("D _f2_compare.py:67,69", D)

# E. _g9_gate.py:157-160
def E(rec):
    bindings = [rec]
    n_reverified = sum(1 for b in bindings if b.get("path"))
    n_match = sum(1 for b in bindings if b.get("match") is True)
    r11_problems = []
    return (n_reverified, n_match, "FAIL" if r11_problems else "PASS")
trial("E _g9_gate.py:157-160", E)

# F. _f2v_final.py:54,57-58
def F(rec):
    pb = [rec]
    collected = sum(1 for b in pb if b.get("path"))
    match = sum(1 for b in pb if b.get("match") is True)
    tiers = {}
    for b in pb:
        if b.get("match") is True:
            tiers[b.get("tier")] = tiers.get(b.get("tier"), 0) + 1
    return (collected, match, tiers)
trial("F _f2v_final.py:54,57-58", F)

# G. _f2w_extract.py:26-33
def G(rec):
    pb = rec
    vp = pb.get("verified_path", "") or ""
    rc = pb.get("recomputed", "") or ""
    return (vp, rc, pb.get("bytes", "-"), pb.get("path"), pb.get("tier"), pb.get("match"))
trial("G _f2w_extract.py:26-33", G)

# H. _f2_repro.py:49
def H(rec):
    return (rec["declared"], rec["path"], rec["match"])
trial("H _f2_repro.py:49", H)

# Z. correct handling: walk members
def Z(rec):
    if rec.get("tier") != "SAMEDOC_LINK_EQ":
        return "not merged"
    out = []
    for mem in rec["members"]:
        p = Path(mem["path"])
        data = p.read_bytes()
        out.append((hashlib.sha256(data).hexdigest() == mem["sha"], len(data) == mem["bytes"]))
    return out
trial("Z walk members (correct branch)", Z)

crashes = sum(1 for _, st, _ in TRIALS if st == "CRASH")
print("\nTOTAL_TRIALS=%d CRASH_COUNT=%d" % (len(TRIALS), crashes))
for n, st, d in TRIALS:
    if st == "CRASH":
        print("  CRASH: %s -> %s" % (n, d))
print("EXIT=0")
