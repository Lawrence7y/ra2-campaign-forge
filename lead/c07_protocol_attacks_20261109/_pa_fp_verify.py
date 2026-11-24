# -*- coding: utf-8 -*-
# _pa_fp_verify.py — 攻防演练：编排方给定 9 件被核对象指纹实算核验（python -I -X utf8 + hashlib）。
# 只读；输出绑定行与 MATCH/MISMATCH。
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EXPECTED = {
    "lead/c07_truth_protocol_20261109/_tp_C07_TRUTH_PROTOCOL.md": (
        "68395681bbfd6b348a91664ec8c0dfafe1b9aa22a939691d0683414071f96547", 25630),
    "lead/c07_truth_protocol_20261109/_tp_TP_ATTESTATION_TEMPLATE.md": (
        "5ae6f5230782596ab93a2e85d06f6bf00190f97e8cad57b78904a42bc6acdaf2", 7873),
    "lead/c07_truth_protocol_20261109/_tp_TP_VERIFIER_CHECKLIST.md": (
        "fe0d6909c49aa6ee30775d77304da88eac924acaab2d13ccbb858c99bf6136b7", 8599),
    "lead/c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md": (
        "5102beae1ecf4952862d4ff1319283df816c53a49bdc81bae38d9709bef974e3", 38232),
    "lead/c07_gate_fix_20261109/_f3_c7check.py": (
        "3ddddc60fca034fe2b6434e0d8baf38c7bc79966342cf287e8521070b2553600", 33118),
    "lead/c07_slot_20261109/_c7_record_template.json": (
        "3d763a8b679370ade8999a23a18679c7296909bf8a020b71694c0ccca7e8b062", 3812),
    "lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json": (
        "d847de88bb0c0c04290c877180a9c45c502df773ba297a36406bffecbe66796b", 27965),
    "lead/PENDING_DECISIONS.md": (
        "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": (
        "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

def main():
    ok = 0
    for rel, (eh, eb) in EXPECTED.items():
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.exists(p):
            print("MISSING %s" % rel)
            continue
        with open(p, "rb") as f:
            data = f.read()
        h = hashlib.sha256(data).hexdigest()
        b = len(data)
        verdict = "MATCH" if (h == eh and b == eb) else "MISMATCH"
        if verdict == "MATCH":
            ok += 1
        print("%s %s 被核对象 SHA256 = %s，字节数 = %d" % (verdict, rel, h, b))
    print("SUMMARY %d/%d MATCH" % (ok, len(EXPECTED)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
