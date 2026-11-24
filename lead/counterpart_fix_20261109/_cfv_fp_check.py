# -*- coding: utf-8 -*-
"""_cfv_fp_check.py — 对照补齐复核员·GLM 指纹复核（只读）
实算 SHA256+bytes，比对：(A) 编排方 12 件基线；(B) 撰写人 15 件绑定值。
绝不写任何被核对象。输出 CSV 风格行。
"""
import hashlib
import sys

REPO = r"D:\Project\ra2-campaign-forge"

# (path, orchestrator_baseline_sha_or_None, orchestrator_baseline_bytes_or_None,
#  writer_claimed_sha_or_None, writer_claimed_bytes_or_None, label)
FILES = [
    ("lead/b2b_design_20261106/STATE_MATRIX.json",
     "1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558,
     "1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558, "乙矩阵"),
    ("lead/b2b_design_20261106/B2B_DESIGN.md",
     "565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf", 66735,
     "565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf", 66735, "乙设计"),
    ("lead/strict_exposure_20261109/STRICT_EXPOSURE.md",
     "3a4b1bb7cf7f0bd501b3e99d575c4907dd0e17f5557dd0b8826e5fb07fe2bdc8", 23798,
     "3a4b1bb7cf7f0bd501b3e99d575c4907dd0e17f5557dd0b8826e5fb07fe2bdc8", 23798, "暴露面交付件"),
    ("lead/strict_exposure_20261109/_se_enum_out.txt",
     "35d27095d697d167892b41f452c9fc3cccb85ef528ee8695266c95220ce023c2", 17870,
     "35d27095d697d167892b41f452c9fc3cccb85ef528ee8695266c95220ce023c2", 17870, "暴露面枚举输出"),
    ("lead/text_fix_unified_20261109/_uf_UNIFIED_FIX_LIST_20261109.md",
     "441b073a39a2ac195d90d43e3ba85f3c2202d5fafce31bec9c96e000a01e0923", 25095,
     "441b073a39a2ac195d90d43e3ba85f3c2202d5fafce31bec9c96e000a01e0923", 25095, "统一清单"),
    ("lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md",
     "0e817ebb8087141de2b974b5587db0a3aa576f30ecb6a19c0ed993404707ec31", 36851,
     "0e817ebb8087141de2b974b5587db0a3aa576f30ecb6a19c0ed993404707ec31", 36851, "A-B裁决件"),
    ("lead/matrix_row5_20261109/MATRIX_ROW5_COUPLING.md",
     "6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8", 29818,
     "6f2b3009b0de33bbe6a3f61e7a0e1c9b6e7e20215ea9c94a45f4c52479811ae8", 29818, "矩阵连带评估件"),
    ("lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py",
     "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759,
     "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759, "候选LF"),
    ("lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md",
     "c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801", 28897,
     "c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801", 28897, "V2定版件"),
    ("out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py",
     "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508,
     "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508, "母本"),
    ("lead/PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419,
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419, "台账一"),
    ("lead/GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518,
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518, "台账二"),
    ("lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md",
     None, None,
     "1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b", 23129, "重签件"),
    ("lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md",
     None, None,
     "96071dd9d58e30a54966a2a1e16f4af918c2f8dd5825363510e8ced8bc6a8fea", 24661, "R3复审"),
    ("lead/matrix_ab_ruling_20261109/_rv2_probe_20261109_out.txt",
     None, None,
     "d78ada307dfad13f18f8d1e89f1eca771d7a4fc660663ef8c4c27c1680510ec6", 7346, "裁决探针输出"),
    # 撰写人自产 4 件（无基线，只实测记录）
    ("lead/counterpart_fix_20261109/_cf_counterpart_vs_tighten_20261109.md",
     None, None, None, 32840, "主交付件"),
    ("lead/counterpart_fix_20261109/_cf_enum_counterpart.py",
     None, None, None, None, "枚举仿真脚本"),
    ("lead/counterpart_fix_20261109/_cf_enum_out.txt",
     None, None, None, 38331, "枚举输出"),
    ("lead/counterpart_fix_20261109/_cf_fp_check.py",
     None, None, None, None, "撰写人指纹脚本"),
]

def main():
    ok_a = ok_b = 0
    n_a = n_b = 0
    for rel, base_sha, base_b, w_sha, w_b, label in FILES:
        p = REPO + "\\" + rel.replace("/", "\\")
        try:
            with open(p, "rb") as f:
                data = f.read()
        except OSError as e:
            print("MISSING\t%s\t%s\t%r" % (label, rel, e))
            continue
        sha = hashlib.sha256(data).hexdigest()
        size = len(data)
        line = "%s\t%s\t%d" % (label, sha, size)
        if base_sha is not None:
            n_a += 1
            m = (sha == base_sha and size == base_b)
            ok_a += 1 if m else 0
            line += "\tORCH=%s" % ("MATCH" if m else "MISMATCH exp=%s/%d" % (base_sha[:12], base_b))
        if w_sha is not None:
            n_b += 1
            m = (sha == w_sha and size == w_b)
            ok_b += 1 if m else 0
            line += "\tWRITER=%s" % ("MATCH" if m else "MISMATCH exp=%s/%d" % (w_sha[:12], w_b))
        print(line)
    print("SUMMARY\torchestrator %d/%d\twriter %d/%d" % (ok_a, n_a, ok_b, n_b))
    sys.stdout.flush()

if __name__ == "__main__":
    main()
