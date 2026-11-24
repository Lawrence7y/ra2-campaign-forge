# -*- coding: utf-8 -*-
# _hdv_fp_extra.py — 复核员补算设计件 §7 绑定行区其余三件指纹（只读）
import hashlib, os, sys

BASE = r"D:\Project\ra2-campaign-forge"
ITEMS = [
    (r"lead\c07_protocol_attacks_20261109\_pa_ATTACK_REPORT.md",
     "4a2f0e860179e4dfd58d26535f09b327481831e31baa2757604b91fb0f1a38e7", 20048),
    (r"lead\c07_truth_protocol_20261109\_tp_TP_ATTESTATION_TEMPLATE.md",
     "5ae6f5230782596ab93a2e85d06f6bf00190f97e8cad57b78904a42bc6acdaf2", 7873),
    (r"lead\c07_hardening_20261109\_hd_carrier_scan.py",
     "8202790fa3d7697e8ce8955fe61510308273bddbf6dc377a4ac6d7c356453957", 3423),
]

n_match = 0
for rel, want_sha, want_bytes in ITEMS:
    p = os.path.join(BASE, rel)
    h = hashlib.sha256(); n = 0
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk); n += len(chunk)
    got = h.hexdigest()
    ok = (got == want_sha) and (n == want_bytes)
    n_match += ok
    print("%s  bytes=%d  sha256=%s  %s" % ("MATCH  " if ok else "MISMATCH", n, got, rel))
print("---")
print("matched %d/%d" % (n_match, len(ITEMS)))
