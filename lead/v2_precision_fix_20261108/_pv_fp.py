# _pv_fp.py — 复核员独立指纹扫描（只读，hashlib，不写任何既有件）
import hashlib
import os

BASE = r"D:\Project\ra2-campaign-forge"
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
    # 候选 R3 文件（待定位确认，先按常见路径试）
    r"lead\b2b_candidate_review3_20261107\REVIEW3_20261107.md",
]

for rel in FILES:
    p = os.path.join(BASE, rel)
    if not os.path.exists(p):
        print("MISSING", rel)
        continue
    with open(p, "rb") as f:
        data = f.read()
    print("被核对象 SHA256 =", hashlib.sha256(data).hexdigest(), ", 字节数 =", len(data), "|", rel)

# 定位 R3 文件（sha 96071dd9 开头，24661 字节）
print("\n--- 定位 R3（24661 字节）---")
for root in [r"lead\b2b_candidate_review3_20261107", r"lead\b2b_candidate_review_20261106",
             r"lead\b2b_candidate_review2_20261106", r"lead\n4_yi_final_20261108"]:
    d = os.path.join(BASE, root)
    if not os.path.isdir(d):
        continue
    for name in os.listdir(d):
        p = os.path.join(d, name)
        if os.path.isfile(p):
            data = open(p, "rb").read()
            h = hashlib.sha256(data).hexdigest()
            tag = " <== R3?" if h.startswith("96071dd9") or len(data) == 24661 else ""
            print(h[:16], len(data), os.path.join(root, name), tag)
