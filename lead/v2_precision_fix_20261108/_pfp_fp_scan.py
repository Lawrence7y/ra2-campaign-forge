# -*- coding: utf-8 -*-
# 修正建议撰写员：上游指纹扫描（只读，hashlib）
import hashlib, os
ROOT = r"D:\Project\ra2-campaign-forge"
FILES = [
    r"lead\n4_yi_final_20261108\_n4v2_B_EXECUTION_SPEC_V2.md",
    r"lead\n4_yi_final_20261108\B_EXECUTION_SPEC_V2_YI.md",
    r"lead\n4_yi_final_20261108\CANDIDATE_RESIGN_YES_V2.md",
    r"lead\b2b_design_20261106\STATE_MATRIX.json",
    r"lead\b2b_design_20261106\B2B_DESIGN.md",
    r"lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py",
    r"lead\b2b_candidate_lf_20261107\CANDIDATE_LF.diff",
    r"out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py",
    r"lead\PENDING_DECISIONS.md",
    r"lead\GOAL_THREE_TARGETS_20261018.md",
    r"lead\b2b_candidate_review3_20261107\CANDIDATE_SEMANTIC_REVIEW_R3.md",
    r"lead\v2_precision_fix_20261108\_pf2_findings_20261109.md",
]
for rel in FILES:
    p = os.path.join(ROOT, rel)
    with open(p, "rb") as f:
        data = f.read()
    h = hashlib.sha256(data).hexdigest()
    print("被核对象 SHA256 = " + h + "，字节数 = " + str(len(data)) + "（" + rel + "）")
    with open(p, "rb") as f:
        n = sum(1 for _ in f)
    print("    行数 = " + str(n))
