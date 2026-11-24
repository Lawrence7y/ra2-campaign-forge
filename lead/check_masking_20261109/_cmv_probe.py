import hashlib
import os
import re

ROOT = "D:/Project/ra2-campaign-forge/"

paths = [
    "lead/d27_ruling_20261106/check_d27.py",
    "lead/d29_ruling_20261106/check_d29.py",
    "lead/d30_ruling_20261106/check_d30.py",
    "lead/refsync_scope_20261109/_rs_carrier_scan.py",
    "lead/masking_effect_20261109/_me_REPORT.md",
    "lead/masking_effect_20261109/MASKING_EFFECT_AUDIT.md",
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
    "lead/check_masking_20261109/_cm_AUDIT.md",
    "lead/check_masking_20261109/_cm_inject.py",
    "lead/check_masking_20261109/_cm_injection_out.txt",
    "lead/check_masking_20261109/_cm_run_console.txt",
    "lead/check_masking_20261109/_cm_rs_broken_out.txt",
]

print("== FINGERPRINTS (hashlib sha256) ==")
for p in paths:
    f = ROOT + p
    if not os.path.isfile(f):
        print("MISSING", p)
        continue
    b = open(f, "rb").read()
    lines = b.count(b"\n")
    print("%-64s bytes=%-9d lines=%-7d sha256=%s" % (p, len(b), lines, hashlib.sha256(b).hexdigest()))

print()
print("== BINDING LINES IN _cm_AUDIT.md ==")
audit = ROOT + "lead/check_masking_20261109/_cm_AUDIT.md"
if os.path.isfile(audit):
    txt = open(audit, "r", encoding="utf-8", errors="replace").read()
    pat = re.compile(r"被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)")
    ms = list(pat.finditer(txt))
    print("binding line matches =", len(ms))
    for m in ms:
        print("  HASH", m.group(1), "BYTES", m.group(2))
    # check strict format: no inserted characters between prefix and hex
    bad = re.findall(r"被核对象 SHA256 = (?!\S{64}，)", txt)
    print("malformed-binding-prefix count =", len(bad))
else:
    print("audit file missing")
