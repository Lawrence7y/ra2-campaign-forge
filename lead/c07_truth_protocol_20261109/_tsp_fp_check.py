# -*- coding: utf-8 -*-
# _tsp_fp_check.py — C07_TRUTH_SELF_PROOF 撰写会话的指纹核验（编排方 11 件上游 + 设计产出 3 件）。
# 只读实算：python -I -X utf8 + 绝对路径 + hashlib；零真机、零采样、无身份值。
import hashlib
import os

ROOT = r"D:\Project\ra2-campaign-forge"

EXPECTED = [
    # (相对路径, 期望 SHA256, 期望字节数, 来源)
    (r"lead\c07_gate_fix_20261109\C07_GATE_G1_G5_FIX.md",
     "fd1ada2fc74afb0fb2aefa9443c45f7ac2c9371594ff60ad39729be5767de4cf", 25770, "编排方"),
    (r"lead\c07_gate_fix_20261109\_f3_c7check.py",
     "3ddddc60fca034fe2b6434e0d8baf38c7bc79966342cf287e8521070b2553600", 33118, "编排方"),
    (r"lead\c07_gate_fix_20261109\_f3_V1_t29variant_consistent.json",
     "57706012fde569c84aaec4eefe36e5c46327ace964bc97a746ca7960bb28e760", 3232, "编排方"),
    (r"lead\c07_gate_audit_20261109\C07_SELFCHECK_AUDIT.md",
     "e45fa323b293d07de2416a0392d3cbb618121d45baeed091f678832a34bf35ab", 33459, "编排方"),
    (r"lead\c07_slot_20261109\C07_IDENTITY_SLOT.md",
     "05ecdfca451476bb80d84281068fcd9c59d1364b2247cb5482943de6417781fc", 20651, "编排方"),
    (r"lead\c07_slot_20261109\_c7_record_template.json",
     "3d763a8b679370ade8999a23a18679c7296909bf8a020b71694c0ccca7e8b062", 3812, "编排方"),
    (r"lead\nextstep_plan_20261106\NEXT_STEPS_20261106.md",
     "c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c", 27225, "编排方"),
    (r"lead\d13d14_cards_20261108\DECISION_QUESTIONS.md",
     "0a709f2da12e0234cd94ff0baf521652e7d1aed6cfd04929b9728adbfd85bf5f", 27172, "编排方"),
    (r"lead\a_residual_n1_20261108\ACCEPTANCE_RECORDS.json",
     "d847de88bb0c0c04290c877180a9c45c502df773ba297a36406bffecbe66796b", 27965, "编排方"),
    (r"lead\PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419, "编排方"),
    (r"lead\GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518, "编排方"),
    (r"lead\c07_truth_protocol_20261109\_tp_C07_TRUTH_PROTOCOL.md",
     "68395681bbfd6b348a91664ec8c0dfafe1b9aa22a939691d0683414071f96547", 25630, "设计绑定行"),
    (r"lead\c07_truth_protocol_20261109\_tp_TP_ATTESTATION_TEMPLATE.md",
     "5ae6f5230782596ab93a2e85d06f6bf00190f97e8cad57b78904a42bc6acdaf2", 7873, "设计绑定行"),
    (r"lead\c07_truth_protocol_20261109\_tp_TP_VERIFIER_CHECKLIST.md",
     "fe0d6909c49aa6ee30775d77304da88eac924acaab2d13ccbb858c99bf6136b7", 8599, "设计绑定行"),
]

ok = 0
for rel, exp_sha, exp_bytes, src in EXPECTED:
    p = os.path.join(ROOT, rel)
    try:
        with open(p, "rb") as f:
            data = f.read()
        sha = hashlib.sha256(data).hexdigest()
        n = len(data)
        m = (sha == exp_sha and n == exp_bytes)
        print("%s  %s  sha256=%s bytes=%d (期望 %s/%d, 来源=%s)"
              % ("MATCH" if m else "MISMATCH", rel, sha, n, exp_sha[:12] + "…", exp_bytes, src))
        ok += 1 if m else 0
    except OSError as e:
        print("ERROR  %s  %s" % (rel, e))

print("TOTAL: %d/%d MATCH" % (ok, len(EXPECTED)))
