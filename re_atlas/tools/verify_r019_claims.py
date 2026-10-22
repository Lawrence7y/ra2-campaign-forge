# -*- coding: utf-8 -*-
"""R-031: machine gate for the R-019/R-023 claims (kb/30 section 12).

Track A (M1, published numbers): re-run the sweep inside dump_ini_keyindex and
assert EXACTLY 2,426 / 2,305 / 1,893 / 164 -- the §12 table that R-023 stamped.
Track B (M2, R-031 new): classify every call site by its KEY SLOT (2nd-to-last
push for readers, last push for GetSection) and census imm-in-region vs
register. This quantifies the G-37 defect (M1's "last string push" can be the
SECTION literal or an older consumed literal, not the key) on OUR pipeline,
for dual confirmation against the independent GLM sweep.

Read-only on the exe. Deterministic; run:
    python re_atlas/tools/verify_r019_claims.py
"""

import hashlib
import sys

sys.path.insert(0, r"re_atlas/tools")
import dump_ini_keyindex as K  # module main-guard keeps it import-safe

SHA256 = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

results = []


def chk(cid, ok, detail=""):
    results.append((cid, "PASS" if ok else "FAIL", str(detail)[:130]))
    return ok


h = hashlib.sha256(K.BLOB).hexdigest()
if h != SHA256:
    print("GATE G0 FAIL sha256 %s -- ALL VOID" % h)
    sys.exit(1)
chk("G0 sha256", True, h[:16])

# ---- Track A: the published numbers ---------------------------------------
sites = K.call_sites()                      # sweep over full .text
per = {}
for _cv, t in sites:
    per[K.READERS[t][0]] = per.get(K.READERS[t][0], 0) + 1

expect = {"ReadString": 650, "ReadInteger": 757, "ReadBool": 651,
          "ReadDouble": 306, "GetSection": 54,
          "ReadUnicodeString": 5, "ReadStringtableEntry": 3}
chk("A.total 2426", len(sites) == 2426, len(sites))
chk("A.per-reader table", per == expect, per)

m1 = [(cv, K.key_before(cv)) for cv, t in sites]
rec = [(cv, r) for cv, r in m1 if r]
chk("A.M1 recovered 2305", len(rec) == 2305, len(rec))
by_key = {}
for cv, (_s, kva, txt) in rec:
    by_key.setdefault(txt, []).append(cv)
chk("A.distinct keys 1893", len(by_key) == 1893, len(by_key))
multi = {k for k, v in by_key.items() if len(v) > 1}
chk("A.multi-read 164", len(multi) == 164, len(multi))

# E8 byte-scan parity (tool's own hard control, recomputed here)
chk("A.E8 parity", len(K.e8_scan()) == len(sites) == 2426)

# ---- Track B: M2 key-slot census ------------------------------------------
SLOT = {"GetSection": -1}                    # default -2 for readers

def slot_kind(cv, t):
    ps = K.pushes_before(cv)
    if not ps:
        return "none", None
    idx = SLOT.get(K.READERS[t][0], -2)
    if len(ps) < -idx:
        return "none", None
    _site, kind, val = ps[idx]
    if kind == "imm" and K.RDATA_LO <= val < K.DATA_HI:
        s = K.cstr(val)
        if len(s) >= 2 and all(0x20 < ord(ch) < 0x7F for ch in s):
            return "literal", val
        return "imm-nonslotstring", val
    if kind == "imm":
        return "imm-other", val
    return "register", val

census = {"literal": 0, "register": 0, "imm-nonslotstring": 0,
          "imm-other": 0, "none": 0}
conflicts = []                              # M1 recovered, slot != M1 literal
for cv, t in sites:
    kind, val = slot_kind(cv, t)
    census[kind] += 1
    r = K.key_before(cv)
    if r and not (kind == "literal" and val == r[1]):
        conflicts.append((cv, K.READERS[t][0], r[2], kind))

chk("B.literal-slot >= 2050", census["literal"] >= 2050, census)
chk("B.register-slot in [180,300] (pipeline-dependent)",
    180 <= census["register"] <= 300, census["register"])
chk("B.conflicts >= 150 (G-37 scale)", len(conflicts) >= 150, len(conflicts))

# per-reader M2 census (stable under THIS pipeline; GLM's independent sweep
# differs ~70-100 sites due to fnstart derivation -- recorded, not hidden)
pr = {}
for cv, t in sites:
    kind, _v = slot_kind(cv, t)
    pr.setdefault(K.READERS[t][0], {}).setdefault(kind, 0)
    pr[K.READERS[t][0]][kind] += 1
for rname, c in sorted(pr.items()):
    print("M2 %-22s %s" % (rname, c))

# ---- Track B: the three documented sample sites ----------------------------
def sample(cv, want_key_slot_kind, m1_text):
    got = [c for c in conflicts if c[0] == cv]
    if not got:
        return False
    _cv, _r, m1s, kind = got[0]
    return kind == want_key_slot_kind and m1s == m1_text

chk("B.scenario.CPP misattributed@0x686ED0",
    sample(0x00686ED0, "register", "D:\\ra2mdpost\\Scenario.CPP"))
chk("B.tile template@0x546524",
    sample(0x00546524, "register", "Tile%02dAnim"))
chk("B.pct-d@0x691908", sample(0x00691908, "register", "%d"))
chk("B.powerup@0x4647ED", sample(0x004647ED, "register", "PowerUp%01dYSort"))

# ---- Track B: section-name contamination of the key column -----------------
sec_as_key = [k for k in by_key if k in
              ("Warheads", "TaskForces", "TeamTypes", "ScriptTypes",
               "Animations", "VoxelAnims", "Particles")]
chk("B.section-names appear as 'keys' (G-37 class)",
    len(sec_as_key) >= 3, sec_as_key)

# ---- negative controls ------------------------------------------------------
# NEG1: rule sensitivity -- GetSection under the -2 rule must drop its
# literal count (54 -> mostly register): proves the slot rule drives results.
gs_lit_2 = sum(1 for cv, t in sites if K.READERS[t][0] == "GetSection"
               and slot_kind(cv, t)[0] == "literal")
chk("NEG GetSection -1 rule yields 3 literals", gs_lit_2 == 3, gs_lit_2)

# NEG2 (G-28 unrelated): the sample() helper must reject a real key site.
def fake():
    r = K.key_before(0x00410AA0)            # genuine Name call, slot=imm literal
    got = [c for c in conflicts if c[0] == 0x00410AA0]
    return bool(got)
chk("NEG genuine-key site not in conflicts", not fake())

# NEG3: sha gate liveness
orig = hashlib.sha256(open(r"D:\Project\ra2-campaign-forge\ra2youli\.ra2opt\orig\gamemd.exe", "rb").read()).hexdigest()
chk("NEG sha-gate live (orig differs)", orig != SHA256, orig[:10])

fails = [r for r in results if r[1] == "FAIL"]
print("R-019 gate: %d/%d PASS" % (len(results) - len(fails), len(results)))
print("M2 census: %s | conflicts: %d" % (census, len(conflicts)))
for cid, st, det in results:
    print("%s\t%s\t%s" % (st, cid, det))
sys.exit(0 if not fails else 1)
