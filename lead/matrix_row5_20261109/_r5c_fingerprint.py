# -*- coding: utf-8 -*-
# _r5c_fingerprint.py — 连带评估交付件（MATRIX_ROW5_COUPLING.md）§2/§5 指纹实算：
# 被核回件本体（_r5_row5_linkage_assessment.md）+ 编排方基线九件，hashlib 实算。
# 零真机、零采样、只读；python -I -X utf8 运行。
import hashlib

BASE = r"D:\Project\ra2-campaign-forge"
FILES = [
    (BASE + r"\lead\matrix_row5_20261109\_r5_row5_linkage_assessment.md",
     "625436050020104bb6e40bd7b1ec0543b22e3e31cb5bb56a12b0480cff64e26f", 14616),
    (BASE + r"\lead\b2b_design_20261106\STATE_MATRIX.json",
     "1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558),
    (BASE + r"\lead\b2b_design_20261106\B2B_DESIGN.md",
     "565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf", 66735),
    (BASE + r"\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py",
     "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759),
    (BASE + r"\lead\n4_yi_final_20261108\_n4v2_B_EXECUTION_SPEC_V2.md",
     "c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801", 28897),
    (BASE + r"\lead\n4_yi_final_20261108\CANDIDATE_RESIGN_YES_V2.md",
     "1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b", 23129),
    (BASE + r"\lead\v2_precision_fix_20261108\V2_PRECISION_FIX_PROPOSAL.md",
     "b1231ccb8b80c5200e2ff33b15e09ae52b0452a1481dfc7989730f7da16eda5b", 22048),
    (BASE + r"\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py",
     "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508),
    (BASE + r"\lead\PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    (BASE + r"\lead\GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]

ok = 0
for i, (path, exp_sha, exp_len) in enumerate(FILES, 1):
    with open(path, "rb") as fh:
        data = fh.read()
    sha = hashlib.sha256(data).hexdigest()
    n = len(data)
    good = (sha == exp_sha and n == exp_len)
    ok += good
    print("被核对象 SHA256 = `%s`，字节数 = %d" % (sha, n))
    print("     [%d/10] %s  期望sha=%s..%s  期望字节=%d  %s"
          % (i, "MATCH" if good else "MISMATCH", exp_sha[:8], exp_sha[-6:],
             exp_len, path))
print("FINGERPRINT_MATCH %d/10" % ok)
