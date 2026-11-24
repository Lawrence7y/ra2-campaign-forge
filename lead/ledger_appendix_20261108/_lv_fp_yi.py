# -*- coding: utf-8 -*-
# _lv_fp_yi.py — 笔4 YI §4 绑定表 11 件指纹独立实算（只读）
import hashlib, os
base = r"D:\Project\ra2-campaign-forge"
rels = [
 r"out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py",
 r"lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py",
 r"lead\b2b_candidate_lf_20261107\CANDIDATE_LF.diff",
 r"lead\b2b_design_20261106\B2B_DESIGN.md",
 r"lead\b2b_design_20261106\STATE_MATRIX.json",
 r"lead\re_line_20261105\B1_HARNESS_PATCH\B2_FIX_DESIGN.md",
 r"lead\b2_preaudit_20261106\B2_PREAUDIT.md",
 r"lead\b2b_preaudit_20261106\B2B_PREAUDIT.md",
 r"lead\b2b_candidate_review3_20261107\CANDIDATE_SEMANTIC_REVIEW_R3.md",
 r"lead\bexec_n4_20261108\B_EXECUTION_SPEC.md",
 r"lead\direction_ruling_20261108\RULING_DIRECTION.md",
]
for rel in rels:
    p = os.path.join(base, rel)
    if not os.path.exists(p):
        print("MISSING", rel); continue
    b = open(p, "rb").read()
    print("%s %8d %s" % (hashlib.sha256(b).hexdigest(), len(b), rel))
