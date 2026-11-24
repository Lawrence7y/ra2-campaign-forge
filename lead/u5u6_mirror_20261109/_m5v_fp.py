# -*- coding: utf-8 -*-
# 复核员独立指纹脚本（只读）：对编排方基线 10 件实算 SHA256 + 字节数
import hashlib, os
BASE = r"D:\Project\ra2-campaign-forge"
FILES = [
    r"lead\b2b_design_20261106\STATE_MATRIX.json",
    r"lead\b2b_design_20261106\B2B_DESIGN.md",
    r"lead\v2_precision_fix_20261108\V2_PRECISION_FIX_PROPOSAL.md",
    r"lead\v2_precision_fix_20261108\_pf2_findings_20261109.md",
    r"lead\matrix_row5_20261109\MATRIX_ROW5_COUPLING.md",
    r"lead\text_fix_unified_20261109\UNIFIED_TEXT_FIX.md",
    r"lead\text_fix_unified_20261109\_uf_UNIFIED_FIX_LIST_20261109.md",
    r"lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py",
    r"lead\PENDING_DECISIONS.md",
    r"lead\GOAL_THREE_TARGETS_20261018.md",
]
for rel in FILES:
    p = os.path.join(BASE, rel)
    with open(p, "rb") as f:
        data = f.read()
    print(rel, "SHA256 =", hashlib.sha256(data).hexdigest(), "字节数 =", len(data))
