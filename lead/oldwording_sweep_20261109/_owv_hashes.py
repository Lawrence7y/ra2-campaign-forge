# -*- coding: utf-8 -*-
"""_owv_hashes.py — 复核员独立实算 11 件 SHA256（编排方 9 件 + 报告 §0 另绑 2 件）。只读，仅 stdout。"""
import hashlib

BASE = r"D:/Project/ra2-campaign-forge"
FILES = [
    "lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md",
    "lead/w2_samecause_20261109/W2_SAME_CAUSE.md",
    "lead/o1prime_reach_20261109/O1PRIME_REACHABILITY.md",
    "lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md",
    "lead/strict_exposure_20261109/STRICT_EXPOSURE.md",
    "lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md",
    "lead/handoff_pack_20261109/APPROVAL_PACK.md",
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
    "lead/strict_exposure_20261109/_se_report.md",
    "lead/matrix_reach_20261109/_mr_REACH_EVIDENCE_20261109.md",
]
for f in FILES:
    with open(BASE + "/" + f, "rb") as fh:
        raw = fh.read()
    print(f"{f}\t{hashlib.sha256(raw).hexdigest()}\t{len(raw)}")
