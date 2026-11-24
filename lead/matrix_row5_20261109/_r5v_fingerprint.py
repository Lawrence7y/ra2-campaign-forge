# -*- coding: utf-8 -*-
# _r5v_fingerprint.py — 复核员独立实算 9 件指纹，与编排方基线核对
import hashlib, os

BASE = r"D:\Project\ra2-campaign-forge"
FILES = [
    r"lead\b2b_design_20261106\STATE_MATRIX.json",
    r"lead\b2b_design_20261106\B2B_DESIGN.md",
    r"lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py",
    r"lead\n4_yi_final_20261108\_n4v2_B_EXECUTION_SPEC_V2.md",
    r"lead\n4_yi_final_20261108\CANDIDATE_RESIGN_YES_V2.md",
    r"lead\v2_precision_fix_20261108\V2_PRECISION_FIX_PROPOSAL.md",
    r"out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py",
    r"lead\PENDING_DECISIONS.md",
    r"lead\GOAL_THREE_TARGETS_20261018.md",
]
# 编排方基线（来自 ask）
BASELINE = [
    ("1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558),
    ("565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf", 66735),
    ("ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759),
    ("c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801", 28897),
    ("1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b", 23129),
    ("b1231ccb8b80c5200e2ff33b15e09ae52b0452a1481dfc7989730f7da16eda5b", 22048),
    ("517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508),
    ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]

n_ok = 0
for i, rel in enumerate(FILES):
    p = os.path.join(BASE, rel)
    with open(p, "rb") as f:
        data = f.read()
    h = hashlib.sha256(data).hexdigest()
    n = len(data)
    exp_h, exp_n = BASELINE[i]
    ok = (h == exp_h and n == exp_n)
    n_ok += ok
    print(("OK  " if ok else "DIFF") + f" [{i+1}/9] {rel}")
    print(f"     mine  sha256={h} bytes={n}")
    if not ok:
        print(f"     orch  sha256={exp_h} bytes={exp_n}")
print(f"FINGERPRINT_MATCH {n_ok}/9")
