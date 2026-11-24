# -*- coding: utf-8 -*-
# O1′ 复核员独立指纹核对（只读；基线取自编排方指纹清单，逐项实算比对）
import hashlib
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
BASE = [
    ("lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py",
     "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759),
    ("lead/b2b_design_20261106/STATE_MATRIX.json",
     "1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558),
    ("lead/b2b_design_20261106/B2B_DESIGN.md",
     "565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf", 66735),
    ("lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md",
     "0e817ebb8087141de2b974b5587db0a3aa576f30ecb6a19c0ed993404707ec31", 36851),
    ("lead/matrix_ab_ruling_20261109/_ab_RULING_MATRIX_AB_20261109.md",
     "a7211b32b1f8b06e9ec34da06257ab9e86b7d0259d9ef8d9d3697a8d79096935", 25984),
    ("lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md",
     "6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8", 29818),
    ("lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md",
     "c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801", 28897),
    ("out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py",
     "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508),
    ("lead/PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]
allok = True
for rel, exp_sha, exp_n in BASE:
    p = ROOT / rel
    b = p.read_bytes()
    sha = hashlib.sha256(b).hexdigest()
    ok = (sha == exp_sha and len(b) == exp_n)
    allok = allok and ok
    print(f"{'MATCH' if ok else 'DIFF!!'} bytes={len(b):>7} sha256={sha}  {rel}")
print("ALL_MATCH" if allok else "SOME_DIFF")
