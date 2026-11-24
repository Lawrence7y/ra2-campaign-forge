# _f3v_fp.py -- reviewer fingerprint check (write domain: c07_gate_fix_20261109)
# read-only on all targets; prints rel path, sha256, byte count
import hashlib, os
BASE = r"D:\Project\ra2-campaign-forge"
targets = [
    "lead/c07_slot_20261109/_c7_selfcheck.py",
    "lead/c07_slot_20261109/_c7_record_template.json",
    "lead/c07_gate_audit_20261109/C07_SELFCHECK_AUDIT.md",
    "lead/c07_gate_audit_20261109/_c7a_independent.py",
    "lead/c07_gate_audit_20261109/_c7a_attack_results.txt",
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
    "lead/c07_gate_fix_20261109/_f3_c7check.py",
]
for rel in targets:
    p = os.path.join(BASE, rel)
    with open(p, "rb") as f:
        b = f.read()
    print(rel, hashlib.sha256(b).hexdigest(), len(b))
print("---samples---")
sd = os.path.join(BASE, "lead/c07_gate_audit_20261109/_c7a_samples")
n = 0
for name in sorted(os.listdir(sd)):
    p = os.path.join(sd, name)
    if not os.path.isfile(p):
        continue
    with open(p, "rb") as f:
        b = f.read()
    n += 1
    print(name, hashlib.sha256(b).hexdigest(), len(b))
print("sample_count", n)
