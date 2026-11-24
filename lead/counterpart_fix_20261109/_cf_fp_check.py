# -*- coding: utf-8 -*-
"""指纹复核：对照编排方给定的 12 件指纹。只读，不做任何修改。"""
import hashlib
import json
import os
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
EXPECTED = {
    "lead/b2b_design_20261106/STATE_MATRIX.json": ("1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558),
    "lead/b2b_design_20261106/B2B_DESIGN.md": ("565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf", 66735),
    "lead/strict_exposure_20261109/STRICT_EXPOSURE.md": ("3a4b1bb7cf7f0bd501b3e99d575c4907dd0e17f5557dd0b8826e5fb07fe2bdc8", 23798),
    "lead/strict_exposure_20261109/_se_enum_out.txt": ("35d27095d697d167892b41f452c9fc3cccb85ef528ee8695266c95220ce023c2", 17870),
    "lead/text_fix_unified_20261109/_uf_UNIFIED_FIX_LIST_20261109.md": ("441b073a39a2ac195d90d43e3ba85f3c2202d5fafce31bec9c96e000a01e0923", 25095),
    "lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md": ("0e817ebb8087141de2b974b5587db0a3aa576f30ecb6a19c0ed993404707ec31", 36851),
    "lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md": ("6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8", 29818),
    "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py": ("ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759),
    "lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md": ("c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801", 28897),
    "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py": ("517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    # 本轮追加实读三件（期望值取自：重签件/R3 = 统一清单 §0 指纹表与裁决件 §2.1 在档值；
    # _rv2_probe 输出 = 本轮 Read 实读后自算基线，用于终跑零漂移比对）
    "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md": ("1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b", 23129),
    "lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md": ("96071dd9d58e30a54966a2a1e16f4af918c2f8dd5825363510e8ced8bc6a8fea", 24661),
    "lead/matrix_ab_ruling_20261109/_rv2_probe_20261109_out.txt": ("d78ada307dfad13f18f8d1e89f1eca771d7a4fc660663ef8c4c27c1680510ec6", 7346),
}

def main():
    ok = 0
    bad = []
    for rel, (exp_sha, exp_bytes) in sorted(EXPECTED.items()):
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            print("MISSING", rel)
            bad.append(rel)
            continue
        with open(p, "rb") as f:
            data = f.read()
        sha = hashlib.sha256(data).hexdigest()
        n = len(data)
        match = (sha == exp_sha and n == exp_bytes)
        if match:
            ok += 1
        else:
            bad.append(rel)
        print(("OK  " if match else "MISMATCH"), rel, "sha256=" + sha, "bytes=" + str(n))
    print("SUMMARY ok=%d total=%d bad=%s" % (ok, len(EXPECTED), bad))
    sys.exit(0 if not bad else 1)

if __name__ == "__main__":
    main()
