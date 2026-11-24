# -*- coding: utf-8 -*-
# _hdv_fp_check.py — 加固落地复核员·GLM 步骤①：独立实算 10 件指纹
# 只读脚本：仅 hashlib 读文件，不写任何被核域。
import hashlib, os, sys

BASE = r"D:\Project\ra2-campaign-forge"

# (相对路径, 编排方声称 sha256, 声称字节数)
ITEMS = [
    (r"lead\c07_hardening_20261109\_hd_HARDENING_PLANS_20261109.md",
     "1f555a36f0f029a78b77e64bd748c2ad244760a3ddae0b7846253c1edfcf5d57", 30628),
    (r"lead\c07_protocol_attacks_20261109\PROTOCOL_ATTACK_TEST.md",
     "4488c8ed82c4ef7848eb85b367c6b2b2b0bab81e9f384afa581e0f44482cb743", 32131),
    (r"lead\c07_protocol_attacks_20261109\_pa_gate_runs.txt",
     "8c48e3db2000e4228d8b8f002ba451b2a88ec2778d5275591bc2f0f0f33f6300", 2249),
    (r"lead\c07_protocol_attacks_20261109\_pa_recon_out.txt",
     "a3bcee6537bb1aef522e24406c77e5984e6303a830a321f15b1a8b249bb0bcae", 44758),
    (r"lead\c07_truth_protocol_20261109\_tp_C07_TRUTH_PROTOCOL.md",
     "68395681bbfd6b348a91664ec8c0dfafe1b9aa22a939691d0683414071f96547", 25630),
    (r"lead\c07_truth_protocol_20261109\_tp_TP_VERIFIER_CHECKLIST.md",
     "fe0d6909c49aa6ee30775d77304da88eac924acaab2d13ccbb858c99bf6136b7", 8599),
    (r"lead\c07_gate_fix_20261109\_f3_c7check.py",
     "3ddddc60fca034fe2b6434e0d8baf38c7bc79966342cf287e8521070b2553600", 33118),
    (r"lead\a_residual_n1_20261108\ACCEPTANCE_RECORDS.json",
     "d847de88bb0c0c04290c877180a9c45c502df773ba297a36406bffecbe66796b", 27965),
    (r"lead\PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    (r"lead\GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]

def main():
    n_match = 0
    for rel, want_sha, want_bytes in ITEMS:
        p = os.path.join(BASE, rel)
        h = hashlib.sha256()
        n = 0
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
                n += len(chunk)
        got = h.hexdigest()
        ok = (got == want_sha) and (n == want_bytes)
        n_match += ok
        print("%s  bytes=%d  sha256=%s  %s" % ("MATCH  " if ok else "MISMATCH", n, got, rel))
    print("---")
    print("matched %d/%d" % (n_match, len(ITEMS)))
    sys.exit(0)

if __name__ == "__main__":
    main()
