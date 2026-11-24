"""_sv_probe_readonly.py — 只读复核探针（seal_v2 可行性评估）
用法: python -I -X utf8 <绝对路径>
不写任何只读域；仅在写域内做一次 ctime/mtime 覆写演示。
"""
import hashlib
import os
import time
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WRITE = ROOT / "lead" / "seal_v2_feasibility_20261109"
TARGETS = [
    r"lead\PENDING_DECISIONS.md",
    r"lead\GOAL_THREE_TARGETS_20261018.md",
    r"lead\ordering_evidence_20261109\ORDERING_EVIDENCE.md",
    r"lead\cert_realcheck_20261109\_cr_seal.json",
    r"lead\cert_realcheck_20261109\_cr_build_seal.py",
    r"lead\cert_realcheck_20261109\_cr_real_verify.py",
    r"lead\falsifiable_no_relax_20261109\_fnr_check.py",
]

print("=== A. SHA256 / BYTES (hashlib) ===")
for rel in TARGETS:
    p = ROOT / rel
    if not p.is_file():
        print("MISSING:", rel)
        continue
    b = p.read_bytes()
    print("复核对象:", rel)
    print("被核对象 SHA256 = " + hashlib.sha256(b).hexdigest() + "，字节数 = " + str(len(b)))

print()
print("=== B. stat: ctime vs mtime on the two cert_realcheck files ===")
for rel in TARGETS[3:5]:
    s = (ROOT / rel).stat()
    print(rel)
    print("  st_ctime =", s.st_ctime, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(s.st_ctime)))
    print("  st_mtime =", s.st_mtime, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(s.st_mtime)))
    print("  mtime-ctime =", round(s.st_mtime - s.st_ctime, 3), "s")

print()
print("=== C. empirical: does st_ctime stay put after an overwrite on this FS? ===")
probe = WRITE / "_sv_ctime_probe.bin"
probe.write_bytes(b"A")
s1 = probe.stat()
time.sleep(1.2)
probe.write_bytes(b"BBBBBBBB")
s2 = probe.stat()
print("  after create : ctime=", s1.st_ctime, "mtime=", s1.st_mtime)
print("  after rewrite: ctime=", s2.st_ctime, "mtime=", s2.st_mtime)
print("  ctime_delta=", round(s2.st_ctime - s1.st_ctime, 3), "mtime_delta=", round(s2.st_mtime - s1.st_mtime, 3))
print("  mtime>ctime after rewrite =", s2.st_mtime > s2.st_ctime)
probe.unlink()

print()
print("=== D. lead/ files with mtime-ctime > 328.7 s ===")
lead = ROOT / "lead"
total = 0
hits = []
for p in lead.rglob("*"):
    if p.is_file():
        total += 1
        try:
            s = p.stat()
            d = s.st_mtime - s.st_ctime
            if d > 328.7:
                hits.append((d, str(p.relative_to(ROOT))))
        except OSError:
            pass
print("  total_files_under_lead =", total)
print("  count_mtime_minus_ctime_gt_328.7 =", len(hits))
for d, r in sorted(hits, reverse=True)[:5]:
    print("   sample", round(d, 1), r)

print()
print("=== E. _fnr_check.py:73-76 (as requested) ===")
fnr = (ROOT / TARGETS[6]).read_text(encoding="utf-8", errors="replace").splitlines()
for i in range(72, min(76, len(fnr))):
    print(f"{i+1}: {fnr[i]}")

print()
print("=== F. ORDERING_EVIDENCE.md lines with M2/M3/signature/ctime/328 keywords ===")
oe = (ROOT / TARGETS[2]).read_text(encoding="utf-8", errors="replace").splitlines()
keys = ["M2", "M3", "signature_sidecars", "n_repo_signature", "ctime", "328", "500", "不可否认", "seal_self_sha", "INTEGRITY_OK_BUT_UNCONFIRMED", "TSA", "透明日志"]
shown = 0
for i, l in enumerate(oe, 1):
    if any(k in l for k in keys) and shown < 90:
        print(f"{i}: {l}")
        shown += 1
print("  (shown", shown, "of", len(oe), "lines)")

print()
print("=== G. _cr_seal.json top-level structure ===")
import json
seal = json.loads((ROOT / TARGETS[3]).read_text(encoding="utf-8"))
print("  top-level keys:", list(seal.keys()))
for k, v in seal.items():
    if isinstance(v, (list, dict)):
        print("   ", k, type(v).__name__, "len=", len(v))
    else:
        print("   ", k, "=", repr(v)[:160])
