# _f3v_variants.py -- reviewer's own degradation + G5-shape + truth-boundary probes
# generates variants from T13_positive.json (read-only source) into _f3v_variants/,
# then runs BOTH checkers on each and prints a table. Read-only elsewhere.
import json, os, subprocess, sys, copy
BASE = r"D:\Project\ra2-campaign-forge"
SRC = os.path.join(BASE, "lead", "c07_gate_audit_20261109", "_c7a_samples", "T13_positive.json")
VD = os.path.join(BASE, "lead", "c07_gate_fix_20261109", "_f3v_variants")
ORIG = os.path.join(BASE, "lead", "c07_slot_20261109", "_c7_selfcheck.py")
ENH = os.path.join(BASE, "lead", "c07_gate_fix_20261109", "_f3_c7check.py")
os.makedirs(VD, exist_ok=True)
base = json.load(open(SRC, encoding="utf-8"))

def w(name, obj):
    p = os.path.join(VD, name)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return p

SID_T13 = "sess_dwf-dwfrun-9f1c2d3e-4a5b-4c6d-8e7f-0a1b2c3d4e5f-actor_1_1"
def set_sid(o, sid):
    o["records"][0]["reviewerSessionId"] = sid
    o["reviewer"]["sessionId"] = sid
    return o

variants = {}
# --- degradation probes: ORIGINAL must block; enhanced must also block ---
v = copy.deepcopy(base); v["records"] = []
variants["FV1_records_zero.json"] = w("FV1_records_zero.json", v)
v = copy.deepcopy(base); v["records"][0]["timestamp"] = 20261109
variants["FV2_ts_int.json"] = w("FV2_ts_int.json", v)
v = copy.deepcopy(base); v["schema"] = "N-1-ACCEPTANCE-RECORDS/1"
variants["FV3_schema_wrong.json"] = w("FV3_schema_wrong.json", v)
v = copy.deepcopy(base)
k0 = "lead/d13d14_cards_20261108/DECISION_QUESTIONS.md"
h, b = v["records"][0]["inputHashes"][k0].split("/")
v["records"][0]["inputHashes"][k0] = ("ab" * 32) + "/" + b
variants["FV4_hash_mismatch.json"] = w("FV4_hash_mismatch.json", v)

# --- G5 shape probes ---
v = copy.deepcopy(base); set_sid(v, "12345")
variants["GV1_sid_digits.json"] = w("GV1_sid_digits.json", v)
v = copy.deepcopy(base); set_sid(v, "sess_dwf-dwfrun-0a1b2c3d-4e5f-4a6b-8c9d-0e1f2a3b4c5d-actor_7_2")
variants["GV2_sid_shape_v4.json"] = w("GV2_sid_shape_v4.json", v)
v = copy.deepcopy(base); set_sid(v, "sess_dwf-dwfrun-0a1b2c3d-4e5f-2a6b-9c9d-0e1f2a3b4c5d-actor_7_2")
variants["GV2b_sid_shape_nonv4.json"] = w("GV2b_sid_shape_nonv4.json", v)
v = copy.deepcopy(base); set_sid(v, "sess_dwf-dwfrun-9F1C2D3E-4A5B-4C6D-8E7F-0A1B2C3D4E5F-actor_1_1")
variants["GV3_sid_upperhex.json"] = w("GV3_sid_upperhex.json", v)
v = copy.deepcopy(base); set_sid(v, "sess_dwf-dwfrun-00000000-0000-0000-0000-000000000000-actor_1_1")
variants["GV4_sid_nil.json"] = w("GV4_sid_nil.json", v)
# wrong group structure (not 8-4-4-4-12)
v = copy.deepcopy(base); set_sid(v, "sess_dwf-dwfrun-123456789012345678901234567890123456-actor_1_1")
variants["GV5_sid_badgroups.json"] = w("GV5_sid_badgroups.json", v)

# --- truth-boundary probe: fabricated shape-compliant consistent ID, all else legal ---
v = copy.deepcopy(base); set_sid(v, "sess_dwf-dwfrun-deadbeef-1234-4abc-8def-0123456789ab-actor_1_1")
variants["TV1_truth_boundary.json"] = w("TV1_truth_boundary.json", v)

# --- G1 patch probe: forged internal role at record layer only ---
v = copy.deepcopy(base); v["records"][0]["reviewerRole"] = "卡顿分流员·GLM（代签）"
variants["TV2_role_forged.json"] = w("TV2_role_forged.json", v)

py = sys.executable
def run(checker, target):
    p = subprocess.run([py, "-I", "-X", "utf8", checker, target], capture_output=True, cwd=BASE)
    return p.returncode, p.stdout.decode("utf-8", "replace")

print("%-28s %-6s %-6s  %s" % ("variant", "ORIG", "ENH", "enh FAIL checks"))
expect = {
    "FV1_records_zero.json": ("BLOCK", "BLOCK"), "FV2_ts_int.json": ("BLOCK", "BLOCK"),
    "FV3_schema_wrong.json": ("BLOCK", "BLOCK"), "FV4_hash_mismatch.json": ("BLOCK", "BLOCK"),
    "GV1_sid_digits.json": ("PASS", "BLOCK"), "GV2_sid_shape_v4.json": ("PASS", "PASS"),
    "GV2b_sid_shape_nonv4.json": ("PASS", "PASS"), "GV3_sid_upperhex.json": ("PASS", "PASS"),
    "GV4_sid_nil.json": ("PASS", "BLOCK"), "GV5_sid_badgroups.json": ("PASS", "BLOCK"),
    "TV1_truth_boundary.json": ("PASS", "PASS"), "TV2_role_forged.json": ("PASS", "BLOCK"),
}
viol = []
for name in sorted(variants):
    p = variants[name]
    rc_o, out_o = run(ORIG, p)
    rc_e, out_e = run(ENH, p)
    fails = [ln.strip()[3:60] for ln in out_e.splitlines() if ln.startswith("  [FAIL]")]
    print("%-28s %-6d %-6d  %s" % (name, rc_o, rc_e, "; ".join(f[:40] for f in fails)))
    exp_o, exp_e = expect[name]
    got_o, got_e = ("BLOCK" if rc_o == 1 else "PASS"), ("BLOCK" if rc_e == 1 else "PASS")
    if (exp_o, exp_e) != (got_o, got_e):
        viol.append((name, exp_o, exp_e, got_o, got_e))
print("---")
print("expectation violations:", len(viol))
for x in viol:
    print("VIOLATION", x)
