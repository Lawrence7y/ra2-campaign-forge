# -*- coding: utf-8 -*-
"""_tpv_fp_check.py — 复核员独立指纹实算：三件被核对象 + 编排方 11 件基线。只读输入，无写盘。"""
import hashlib, os, sys

BASE = r"D:\Project\ra2-campaign-forge"

TARGETS = [
    # (相对路径, 回件/编排方声称的 sha256, 声称字节数)
    (r"lead\c07_truth_protocol_20261109\_tp_C07_TRUTH_PROTOCOL.md",
     "68395681bbfd6b348a91664ec8c0dfafe1b9aa22a939691d0683414071f96547", 25630),
    (r"lead\c07_truth_protocol_20261109\_tp_TP_ATTESTATION_TEMPLATE.md",
     "5ae6f5230782596ab93a2e85d06f6bf00190f97e8cad57b78904a42bc6acdaf2", 7873),
    (r"lead\c07_truth_protocol_20261109\_tp_TP_VERIFIER_CHECKLIST.md",
     "fe0d6909c49aa6ee30775d77304da88eac924acaab2d13ccbb858c99bf6136b7", 8599),
    # 编排方基线 11 件
    (r"lead\c07_gate_fix_20261109\C07_GATE_G1_G5_FIX.md",
     "fd1ada2fc74afb0fb2aefa9443c45f7ac2c9371594ff60ad39729be5767de4cf", 25770),
    (r"lead\c07_gate_fix_20261109\_f3_c7check.py",
     "3ddddc60fca034fe2b6434e0d8baf38c7bc79966342cf287e8521070b2553600", 33118),
    (r"lead\c07_gate_fix_20261109\_f3_V1_t29variant_consistent.json",
     "57706012fde569c84aaec4eefe36e5c46327ace964bc97a746ca7960bb28e760", 3232),
    (r"lead\c07_gate_audit_20261109\C07_SELFCHECK_AUDIT.md",
     "e45fa323b293d07de2416a0392d3cbb618121d45baeed091f678832a34bf35ab", 33459),
    (r"lead\c07_slot_20261109\C07_IDENTITY_SLOT.md",
     "05ecdfca451476bb80d84281068fcd9c59d1364b2247cb5482943de6417781fc", 20651),
    (r"lead\c07_slot_20261109\_c7_record_template.json",
     "3d763a8b679370ade8999a23a18679c7296909bf8a020b71694c0ccca7e8b062", 3812),
    (r"lead\nextstep_plan_20261106\NEXT_STEPS_20261106.md",
     "c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c", 27225),
    (r"lead\d13d14_cards_20261108\DECISION_QUESTIONS.md",
     "0a709f2da12e0234cd94ff0baf521652e7d1aed6cfd04929b9728adbfd85bf5f", 27172),
    (r"lead\a_residual_n1_20261108\ACCEPTANCE_RECORDS.json",
     "d847de88bb0c0c04290c877180a9c45c502df773ba297a36406bffecbe66796b", 27965),
    (r"lead\PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    (r"lead\GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]

def main():
    n_match = 0
    n_total = 0
    for rel, claimed_sha, claimed_bytes in TARGETS:
        n_total += 1
        full = os.path.join(BASE, rel)
        if not os.path.isfile(full):
            print("MISSING\t" + rel)
            continue
        with open(full, "rb") as f:
            data = f.read()
        sha = hashlib.sha256(data).hexdigest()
        nbytes = len(data)
        sha_ok = (sha == claimed_sha)
        b_ok = (nbytes == claimed_bytes)
        tag = "MATCH" if (sha_ok and b_ok) else "MISMATCH"
        if tag == "MATCH":
            n_match += 1
        print("%s\t%s\tbytes=%d (claimed %d) sha=%s" % (tag, rel, nbytes, claimed_bytes, sha))
    print("SUMMARY: %d/%d MATCH" % (n_match, n_total))

if __name__ == "__main__":
    main()
