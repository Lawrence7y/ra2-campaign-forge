# -*- coding: utf-8 -*-
# _pav_fp_verify.py — 复核员独立指纹核验（只读；输出到 stdout）
# 核对编排方 9 件基线 + 攻击回件主报告；并扫只读域有无 _pa_/_pav_ 泄漏件。
import hashlib, os, sys, json

BASE = r"D:\Project\ra2-campaign-forge"
EXPECT = {
    r"lead\c07_truth_protocol_20261109\_tp_C07_TRUTH_PROTOCOL.md":
        ("68395681bbfd6b348a91664ec8c0dfafe1b9aa22a939691d0683414071f96547", 25630),
    r"lead\c07_truth_protocol_20261109\_tp_TP_ATTESTATION_TEMPLATE.md":
        ("5ae6f5230782596ab93a2e85d06f6bf00190f97e8cad57b78904a42bc6acdaf2", 7873),
    r"lead\c07_truth_protocol_20261109\_tp_TP_VERIFIER_CHECKLIST.md":
        ("fe0d6909c49aa6ee30775d77304da88eac924acaab2d13ccbb858c99bf6136b7", 8599),
    r"lead\c07_truth_protocol_20261109\C07_TRUTH_SELF_PROOF.md":
        ("5102beae1ecf4952862d4ff1319283df816c53a49bdc81bae38d9709bef974e3", 38232),
    r"lead\c07_gate_fix_20261109\_f3_c7check.py":
        ("3ddddc60fca034fe2b6434e0d8baf38c7bc79966342cf287e8521070b2553600", 33118),
    r"lead\c07_slot_20261109\_c7_record_template.json":
        ("3d763a8b679370ade8999a23a18679c7296909bf8a020b71694c0ccca7e8b062", 3812),
    r"lead\a_residual_n1_20261108\ACCEPTANCE_RECORDS.json":
        ("d847de88bb0c0c04290c877180a9c45c502df773ba297a36406bffecbe66796b", 27965),
    r"lead\PENDING_DECISIONS.md":
        ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    r"lead\GOAL_THREE_TARGETS_20261018.md":
        ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    # 攻击回件主报告（本次复核的被核对象）
    r"lead\c07_protocol_attacks_20261109\_pa_ATTACK_REPORT.md": None,
}

print("== PART 1: fingerprints ==")
match = 0; mismatch = 0
for rel, exp in EXPECT.items():
    p = os.path.join(BASE, rel)
    try:
        data = open(p, "rb").read()
    except OSError as e:
        print("READFAIL", rel, e); mismatch += 1; continue
    h = hashlib.sha256(data).hexdigest()
    n = len(data)
    if exp is None:
        print("SUBJECT %s sha256=%s bytes=%d" % (rel, h, n))
    else:
        ok = (h == exp[0]) and (n == exp[1])
        print("%s sha256=%s bytes=%d expect=(%s,%d) %s"
              % (rel, h, n, exp[0], exp[1], "MATCH" if ok else "MISMATCH"))
        match += 1 if ok else 0
        mismatch += 0 if ok else 1
print("SUMMARY baseline_files=%d match=%d mismatch=%d" % (9, match, mismatch))

print("== PART 2: leakage scan (readonly dirs must contain no _pa_/_pav_) ==")
RO_DIRS = [
    r"lead\c07_truth_protocol_20261109",
    r"lead\c07_gate_fix_20261109",
    r"lead\c07_gate_audit_20261109",
    r"lead\c07_slot_20261109",
]
leak = []
for d in RO_DIRS:
    for root, dirs, files in os.walk(os.path.join(BASE, d)):
        for f in files:
            if f.startswith("_pa_") or f.startswith("_pav_"):
                leak.append(os.path.join(root, f))
print("leaked=%d %s" % (len(leak), leak))

print("== PART 3: all files in readonly dirs with mtime (informational) ==")
for d in RO_DIRS:
    for root, dirs, files in os.walk(os.path.join(BASE, d)):
        dirs[:] = [x for x in dirs if x not in (".mimosa", "__pycache__")]
        for f in sorted(files):
            p = os.path.join(root, f)
            st = os.stat(p)
            import datetime
            mt = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%dT%H:%M:%S")
            print("%s %8d %s" % (mt, st.st_size, os.path.relpath(p, BASE)))
