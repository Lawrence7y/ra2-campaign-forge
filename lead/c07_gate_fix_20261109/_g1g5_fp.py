# -*- coding: utf-8 -*-
# _g1g5_fp.py — 报告撰写员的独立指纹核验（hashlib 实算）。
# 只读；对照编排方任务书给出的指纹与字节数。输出 PASS/FAIL 逐行。
import hashlib
import json
import os

ROOT = r"D:\Project\ra2-campaign-forge"
EXPECT = [
    ("lead/c07_slot_20261109/_c7_selfcheck.py",
     "74bec4d48498903df08dbf3a56ba942e74b58f5b4a7940c094eafdeb03adbf2e", 9961),
    ("lead/c07_slot_20261109/_c7_record_template.json",
     "3d763a8b679370ade8999a23a18679c7296909bf8a020b71694c0ccca7e8b062", 3812),
    ("lead/c07_gate_audit_20261109/C07_SELFCHECK_AUDIT.md",
     "e45fa323b293d07de2416a0392d3cbb618121d45baeed091f678832a34bf35ab", 33459),
    ("lead/c07_gate_audit_20261109/_c7a_independent.py",
     "53082d91ce34f76877b08061503795b8d50b0bcbfac036cc0df6e9b67e7d5610", 17998),
    ("lead/c07_gate_audit_20261109/_c7a_attack_results.txt",
     "3a1b3b9aeb2da4b84ef2e3f0eaa4cf5c6a7fc11d8d1bab415fd0cb079081325d", 137772),
    ("lead/PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    # 本任务被核交付件（修补回件绑定行口径）
    ("lead/c07_gate_fix_20261109/_f3_c7check.py",
     "3ddddc60fca034fe2b6434e0d8baf38c7bc79966342cf287e8521070b2553600", 33118),
]

EXPECT_SAMPLE_BYTES = {
    "T01_empty_trio.json": 3120, "T02a_sid_unknown.json": 3177,
    "T02b_sid_todo.json": 3174, "T02c_sid_na.json": 3173,
    "T03_sid_copied_n1r2.json": 3232, "T04_n11_no_registration.json": 3216,
    "T05_n11_registered_gap.json": 3325, "T06a_role_kadun.json": 3222,
    "T06b_role_fenliu.json": 3223, "T06c_role_fuhe.json": 3217,
    "T07_sid_placeholder.json": 3193, "T08a_records_zero.json": 2280,
    "T08b_records_two.json": 4184, "T09a_container_missing_grade.json": 3207,
    "T09b_container_extra_key.json": 3317, "T10_field_order.json": 3232,
    "T11a_ts_bad.json": 3226, "T11b_ts_int.json": 3213,
    "T11c_ts_text.json": 3219, "T12a_hash_wrong_hex.json": 3232,
    "T12b_hash_wrong_bytes.json": 3232, "T12c_hash_missing_binding.json": 3094,
    "T13_positive.json": 3232, "T14_decision_approve_scope.json": 3235,
    "T16_decisionsemantics_tampered.json": 3235, "T17_artifacthash_fake.json": 3370,
    "T18a_sid_dash.json": 3171, "T18b_sid_digits.json": 3175,
    "T19_sid_nearcopy.json": 3233, "T20_n11_decorated.json": 3231,
    "T22_fullwidth_placeholder.json": 3197, "T23_unresolved_wrong_phrase.json": 3300,
    "T24_inputhash_extra_fake.json": 3370, "T26_container_role_fuhe.json": 3217,
    "T27_grade_approve_scope.json": 3235, "T29_sid_fabricated_shape.json": 3232,
}


def fp(rel):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    with open(p, "rb") as f:
        d = f.read()
    return hashlib.sha256(d).hexdigest(), len(d)


def main():
    n_ok = 0
    for rel, h, b in EXPECT:
        got_h, got_b = fp(rel)
        ok = (got_h == h and got_b == b)
        n_ok += ok
        print("[%s] %s sha=%s… bytes=%d (期望 %s…/%d)"
              % ("OK" if ok else "MISMATCH", rel, got_h[:8], got_b, h[:8], b))
    sdir = os.path.join(ROOT, "lead", "c07_gate_audit_20261109", "_c7a_samples")
    files = sorted(x for x in os.listdir(sdir) if x.endswith(".json"))
    print("样本目录文件数=%d" % len(files))
    s_ok = 0
    for name in files:
        got_b = os.path.getsize(os.path.join(sdir, name))
        exp_b = EXPECT_SAMPLE_BYTES.get(name)
        ok = (exp_b == got_b)
        s_ok += ok
        if not ok:
            print("[MISMATCH] %s bytes=%d 期望=%r" % (name, got_b, exp_b))
    print("样本字节数相符=%d/%d" % (s_ok, len(files)))
    print("保护件指纹相符=%d/%d" % (n_ok, len(EXPECT)))
    return 0 if (n_ok == len(EXPECT) and s_ok == len(files)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
