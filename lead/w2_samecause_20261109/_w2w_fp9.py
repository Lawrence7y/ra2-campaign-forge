# -*- coding: utf-8 -*-
"""W2_SAME_CAUSE.md 交付轮：九件上游指纹本轮独立实算（hashlib），对照编排方基线。纯只读。"""
import hashlib
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
BASELINE = {
    "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py":
        ("ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759),
    "lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md":
        ("cd03a91aac610cd0e7d6f3c70008d5a8d351896173aa0ee9d5d035675f2746d6", 27825),
    "lead/matrix_reach_20261109/_mr_REACH_EVIDENCE_20261109.md":
        ("67d0fc90ceae277f23d43f80484da9445a6385994752a882d04a8517809f10e9", 20820),
    "lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md":
        ("0e817ebb8087141de2b974b5587db0a3aa576f30ecb6a19c0ed993404707ec31", 36851),
    "lead/b2b_design_20261106/STATE_MATRIX.json":
        ("1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558),
    "lead/b2b_design_20261106/B2B_DESIGN.md":
        ("565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf", 66735),
    "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py":
        ("517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508),
    "lead/PENDING_DECISIONS.md":
        ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md":
        ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

ok = 0
for i, (rel, (want_sha, want_n)) in enumerate(BASELINE.items(), 1):
    p = ROOT / rel
    try:
        blob = p.read_bytes()
    except Exception as exc:
        print(f"[{i}/9] {rel} : READ_FAIL {type(exc).__name__}: {exc}")
        continue
    got_sha = hashlib.sha256(blob).hexdigest()
    got_n = len(blob)
    verdict = "MATCH" if (got_sha == want_sha and got_n == want_n) else "MISMATCH"
    if verdict == "MATCH":
        ok += 1
    print(f"[{i}/9] {verdict} bytes={got_n} sha256={got_sha} :: {rel}")

print(f"TOTAL {ok}/9 MATCH")
sys.exit(0 if ok == 9 else 1)
