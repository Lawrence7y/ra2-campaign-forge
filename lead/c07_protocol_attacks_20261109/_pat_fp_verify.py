# -*- coding: utf-8 -*-
# _pat_fp_verify.py —— PROTOCOL_ATTACK_TEST 撰写会话指纹复算（只读；hashlib 实算）
# 运行：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/c07_protocol_attacks_20261109/_pat_fp_verify.py
import hashlib, os, sys

ROOT = r"D:\Project\ra2-campaign-forge"

# 编排方任务书给定的九件指纹（逐字照录，作为期望值）
EXPECTED = [
    ("lead/c07_truth_protocol_20261109/_tp_C07_TRUTH_PROTOCOL.md",
     "68395681bbfd6b348a91664ec8c0dfafe1b9aa22a939691d0683414071f96547", 25630),
    ("lead/c07_truth_protocol_20261109/_tp_TP_ATTESTATION_TEMPLATE.md",
     "5ae6f5230782596ab93a2e85d06f6bf00190f97e8cad57b78904a42bc6acdaf2", 7873),
    ("lead/c07_truth_protocol_20261109/_tp_TP_VERIFIER_CHECKLIST.md",
     "fe0d6909c49aa6ee30775d77304da88eac924acaab2d13ccbb858c99bf6136b7", 8599),
    ("lead/c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md",
     "5102beae1ecf4952862d4ff1319283df816c53a49bdc81bae38d9709bef974e3", 38232),
    ("lead/c07_gate_fix_20261109/_f3_c7check.py",
     "3ddddc60fca034fe2b6434e0d8baf38c7bc79966342cf287e8521070b2553600", 33118),
    ("lead/c07_slot_20261109/_c7_record_template.json",
     "3d763a8b679370ade8999a23a18679c7296909bf8a020b71694c0ccca7e8b062", 3812),
    ("lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json",
     "d847de88bb0c0c04290c877180a9c45c502df773ba297a36406bffecbe66796b", 27965),
    ("lead/PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]

# 复核回件绑定行所绑对象（复核 JSON 逐字：4a2f…38e7 / 20048）
REVIEW_BOUND = ("lead/c07_protocol_attacks_20261109/_pa_ATTACK_REPORT.md",
                "4a2f0e860179e4dfd58d26535f09b327481831e31baa2757604b91fb0f1a38e7", 20048)


def fp(rel):
    p = os.path.join(ROOT, rel)
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(65536)
            if not b:
                break
            h.update(b)
            n += len(b)
    return h.hexdigest(), n


def check(rel, want_sha, want_bytes):
    try:
        sha, n = fp(rel)
    except OSError as e:
        print("MISSING", rel, e)
        return False
    ok = (sha == want_sha) and (n == want_bytes)
    print("%s sha256=%s bytes=%d  expect=%s/%d  %s" % (rel, sha, n, want_sha, want_bytes,
                                                       "MATCH" if ok else "MISMATCH"))
    return ok


def main():
    results = [check(r, s, b) for (r, s, b) in EXPECTED]
    print("---")
    rb = check(*REVIEW_BOUND)
    print("---")
    print("UPSTREAM %d/%d MATCH" % (sum(results), len(results)))
    print("REVIEW-BINDING " + ("MATCH" if rb else "MISMATCH"))
    return 0 if (all(results) and rb) else 1


if __name__ == "__main__":
    sys.exit(main())
