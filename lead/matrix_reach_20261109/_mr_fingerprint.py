# -*- coding: utf-8 -*-
"""_mr_fingerprint.py — 编排方下发 7 件基线指纹复算（hashlib 实算，纯只读）。

纪律：python -I -X utf8 + 绝对路径；只读，不写任何被核对象。
"""
import hashlib
from pathlib import Path

BASE = Path(r"D:\Project\ra2-campaign-forge")
EXPECT = {
    "lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md":
        ("6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8", 29818),
    "lead/matrix_row5_20261109/_r5v_probe_out.txt":
        ("ce84dbd5c8f3eb4386737e994447414a137ed2513d53ef977451f7700ff089c1", 12979),
    "lead/b2b_design_20261106/STATE_MATRIX.json":
        ("1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558),
    "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py":
        ("ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759),
    "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py":
        ("517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508),
    "lead/PENDING_DECISIONS.md":
        ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md":
        ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

n_match = 0
for rel, (exp_sha, exp_bytes) in EXPECT.items():
    p = BASE / rel
    raw = p.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    ok = (sha == exp_sha) and (len(raw) == exp_bytes)
    n_match += 1 if ok else 0
    print(f"[{'MATCH' if ok else 'MISMATCH'}] {rel}")
    print(f"    sha256={sha}  bytes={len(raw)}  (expect {exp_sha} / {exp_bytes})")
print(f"FINGERPRINT_MATCH {n_match}/{len(EXPECT)}")
