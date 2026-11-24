# -*- coding: utf-8 -*-
# _cv_hashes_20261108.py — 重签复核员·GLM 独立实算指纹（只读，不写任何被核文件）
import hashlib, os

BASE = "D:/Project/ra2-campaign-forge/"

BASELINE = [
    ("master",   "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py",
     "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508),
    ("candidate","lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py",
     "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759),
    ("diff",     "lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff",
     "72b108021637cf7d225a9b109a542ec10c934abb1a8e40b8850a82c6bea9cdb9", 18454),
    ("design",   "lead/b2b_design_20261106/B2B_DESIGN.md",
     "565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf", 66735),
    ("matrix",   "lead/b2b_design_20261106/STATE_MATRIX.json",
     "1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558),
    ("v2spec",   "lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md",
     "c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801", 28897),
    ("v2yi",     "lead/n4_yi_final_20261108/B_EXECUTION_SPEC_V2_YI.md",
     "27f31bf560e9a71c5e9603d81a860233e7fc7b19e504eed4a15ea24a2077b067", 35486),
    ("supersede","lead/b2b_yi_supersede_20261108/YI_SUPERSEDE_JIA_BINDING.md",
     "255356ca789955cc2c084388f547a1435feb310f210617b988f761e7ff331c7b", 7344),
    ("ruling",   "lead/direction_ruling_20261108/RULING_DIRECTION.md",
     "0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653", 16514),
    ("r3",       "lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md",
     "96071dd9d58e30a54966a2a1e16f4af918c2f8dd5825363510e8ced8bc6a8fea", 24661),
    ("pending",  "lead/PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("goal3",    "lead/GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]

EXTRAS = [
    ("n4_original", "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md",
     "c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c", 27225),
    ("ast_rerun",   "lead/n4_yi_final_20261108/_n4v2_ast_rerun_out.txt",
     "9986fc2e335afa0748bfd9164c58c3eb04127c2f3db27b4e9fd91d5ee3cafdb6", 22510),
    ("ast_scan",    "lead/bexec_n4_20261108/_n4_ast_scan_out.txt",
     "9986fc2e335afa0748bfd9164c58c3eb04127c2f3db27b4e9fd91d5ee3cafdb6", 22510),
]

REVIEW = "lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md"  # 被核对象：审阅回件

def h(p):
    b = open(p, "rb").read()
    return hashlib.sha256(b).hexdigest(), len(b)

fails = 0
print("== 编排方基线 12 件（自算 → 对照） ==")
for name, rel, exp, eb in BASELINE:
    got, gb = h(BASE + rel)
    ok = (got == exp and gb == eb)
    if not ok: fails += 1
    print("[%s] %-10s sha256=%s bytes=%d  expect=%s/%d  %s" %
          ("PASS" if ok else "FAIL", name, got, gb, exp[:16] + "...", eb, rel))

print("== 附加件（审阅回件声称的绑定值） ==")
for name, rel, exp, eb in EXTRAS:
    got, gb = h(BASE + rel)
    ok = (got == exp and gb == eb)
    if not ok: fails += 1
    print("[%s] %-10s sha256=%s bytes=%d  expect=%s/%d" %
          ("PASS" if ok else "FAIL", name, got, gb, exp[:16] + "...", eb))

print("== 被核对象：审阅回件 ==")
rh, rb = h(BASE + REVIEW)
print("review file sha256=%s bytes=%d" % (rh, rb))

print("== ast_rerun vs ast_scan 逐字节相等 ==")
b1 = open(BASE + EXTRAS[1][1], "rb").read()
b2 = open(BASE + EXTRAS[2][1], "rb").read()
print("byte-equal:", b1 == b2, "len:", len(b1), len(b2))

print("== 行尾风格 ==")
mb = open(BASE + BASELINE[0][1], "rb").read()
cb = open(BASE + BASELINE[1][1], "rb").read()
print("master CR count:", mb.count(b"\r"), "cand CR count:", cb.count(b"\r"))
print("TOTAL FAIL:", fails)
