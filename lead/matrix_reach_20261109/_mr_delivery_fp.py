# -*- coding: utf-8 -*-
"""交付轮指纹实算（2026-11-09，MATRIX_DEFECT_REACHABILITY.md §2 依据）。
纯只读 hashlib 实算：7 件上游基线 + 5 件既有证据件。零写、零进程操作。
"""
import hashlib
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")

BASELINE = {
    "candidate_lf":      r"lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py",
    "matrix_coupling":   r"lead\matrix_row5_20261109\MATRIX_ROW5_COUPLING.md",
    "r5v_probe_out":     r"lead\matrix_row5_20261109\_r5v_probe_out.txt",
    "state_matrix_json": r"lead\b2b_design_20261106\STATE_MATRIX.json",
    "qc151_trip_src":    r"out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py",
    "pending_decisions": r"lead\PENDING_DECISIONS.md",
    "goal_three_targets": r"lead\GOAL_THREE_TARGETS_20261018.md",
}
EVIDENCE = {
    "writer_report":  r"lead\matrix_reach_20261109\_mr_REACH_EVIDENCE_20261109.md",
    "writer_probe_py": r"lead\matrix_reach_20261109\_mr_probe1.py",
    "writer_probe_out": r"lead\matrix_reach_20261109\_mr_probe1_out.txt",
    "reviewer_probe_out": r"lead\matrix_reach_20261109\_mrv_probe1_out.txt",
    "reviewer_fp_out": r"lead\matrix_reach_20261109\_mrv_fp_out.txt",
}

def fp(rel):
    p = ROOT / rel
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)

print("MR_DELIV_FP_START")
for name, rel in BASELINE.items():
    h, n = fp(rel)
    print(f"FP {name} {h} {n}")
for name, rel in EVIDENCE.items():
    h, n = fp(rel)
    print(f"FP {name} {h} {n}")
print("MR_DELIV_FP_DONE")
