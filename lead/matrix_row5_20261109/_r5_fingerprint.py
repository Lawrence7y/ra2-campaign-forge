# -*- coding: utf-8 -*-
"""_r5_ 指纹核对：只读 hashlib，不写任何被核对象。"""
import hashlib

FILES = [
    r"D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\STATE_MATRIX.json",
    r"D:\Project\ra2-campaign-forge\lead\b2b_design_20261106\B2B_DESIGN.md",
    r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py",
    r"D:\Project\ra2-campaign-forge\lead\n4_yi_final_20261108\_n4v2_B_EXECUTION_SPEC_V2.md",
    r"D:\Project\ra2-campaign-forge\lead\n4_yi_final_20261108\CANDIDATE_RESIGN_YES_V2.md",
    r"D:\Project\ra2-campaign-forge\lead\v2_precision_fix_20261108\V2_PRECISION_FIX_PROPOSAL.md",
    r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py",
    r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md",
    r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md",
]

for f in FILES:
    with open(f, "rb") as fh:
        b = fh.read()
    print(f"bytes={len(b)}  sha256={hashlib.sha256(b).hexdigest()}  {f}")
