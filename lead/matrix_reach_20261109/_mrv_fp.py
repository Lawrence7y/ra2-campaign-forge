# -*- coding: utf-8 -*-
"""_mrv_fp.py — 复核员独立指纹实算（零写、只读被核件）。"""
import hashlib
import os
import sys

BASE = r"D:\Project\ra2-campaign-forge"
FILES = [
    ("candidate_lf", r"lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py"),
    ("matrix_coupling", r"lead\matrix_row5_20261109\MATRIX_ROW5_COUPLING.md"),
    ("r5v_probe_out", r"lead\matrix_row5_20261109\_r5v_probe_out.txt"),
    ("state_matrix_json", r"lead\b2b_design_20261106\STATE_MATRIX.json"),
    ("qc151_trip_src", r"out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py"),
    ("pending_decisions", r"lead\PENDING_DECISIONS.md"),
    ("goal_three_targets", r"lead\GOAL_THREE_TARGETS_20261018.md"),
    ("writer_report", r"lead\matrix_reach_20261109\_mr_REACH_EVIDENCE_20261109.md"),
    ("writer_probe1_py", r"lead\matrix_reach_20261109\_mr_probe1.py"),
    ("writer_probe1_out", r"lead\matrix_reach_20261109\_mr_probe1_out.txt"),
    ("writer_fp_py", r"lead\matrix_reach_20261109\_mr_fingerprint.py"),
    ("writer_fp_out", r"lead\matrix_reach_20261109\_mr_fingerprint_out.txt"),
]

BASELINE = {
    "candidate_lf": ("ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759),
    "matrix_coupling": ("6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8", 29818),
    "r5v_probe_out": ("ce84dbd5c8f3eb4386737e994447414a137ed2513d53ef977451f7700ff089c1", 12979),
    "state_matrix_json": ("1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558),
    "qc151_trip_src": ("517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508),
    "pending_decisions": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "goal_three_targets": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

print("MRV_FP_START")
n_match = 0
n_base = 0
for key, rel in FILES:
    p = os.path.join(BASE, rel)
    try:
        with open(p, "rb") as fh:
            blob = fh.read()
        sha = hashlib.sha256(blob).hexdigest()
        line = "FP %-22s %s %d" % (key, sha, len(blob))
        if key in BASELINE:
            n_base += 1
            bsha, bsz = BASELINE[key]
            ok = (sha == bsha and len(blob) == bsz)
            if ok:
                n_match += 1
            line += "  BASELINE_MATCH=%s" % ok
        print(line)
    except OSError as exc:
        print("FP %-22s ERROR %s" % (key, exc))
print("MRV_FP_SUMMARY baseline=%d match=%d" % (n_base, n_match))
print("MRV_FP_DONE")
