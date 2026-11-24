# _ufv_fp_check.py — 复核员独立指纹实算（只读）
# 用法: python -I -X utf8 _ufv_fp_check.py
import hashlib, os

ROOT = r"D:\Project\ra2-campaign-forge"
FILES = [
    # 编排方基线 12 件
    r"lead\b2b_design_20261106\STATE_MATRIX.json",
    r"lead\b2b_design_20261106\B2B_DESIGN.md",
    r"lead\v2_precision_fix_20261108\V2_PRECISION_FIX_PROPOSAL.md",
    r"lead\matrix_row5_20261109\MATRIX_ROW5_COUPLING.md",
    r"lead\o1prime_reach_20261109\O1PRIME_REACHABILITY.md",
    r"lead\w2_samecause_20261109\W2_SAME_CAUSE.md",
    r"lead\matrix_ab_ruling_20261109\RULING_MATRIX_AB.md",
    r"lead\n4_yi_final_20261108\_n4v2_B_EXECUTION_SPEC_V2.md",
    r"lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py",
    r"out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py",
    r"lead\PENDING_DECISIONS.md",
    r"lead\GOAL_THREE_TARGETS_20261018.md",
    # 汇总回件证据引用但不在基线内的件
    r"lead\v2_precision_fix_20261108\_pf2_findings_20261109.md",
    r"lead\n4_yi_final_20261108\CANDIDATE_RESIGN_YES_V2.md",
    r"lead\matrix_reach_20261109\MATRIX_DEFECT_REACHABILITY.md",
    r"lead\b2b_candidate_review3_20261107\CANDIDATE_SEMANTIC_REVIEW_R3.md",
    r"lead\b2b_candidate_lf_20261107\CANDIDATE_LF.diff",
    # 被核对象（唯一新增件）
    r"lead\text_fix_unified_20261109\_uf_UNIFIED_FIX_LIST_20261109.md",
]

for rel in FILES:
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        print(f"MISSING\t{rel}")
        continue
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(65536)
            if not b:
                break
            h.update(b)
            n += len(b)
    print(f"{h.hexdigest()}\t{n}\t{rel}")
