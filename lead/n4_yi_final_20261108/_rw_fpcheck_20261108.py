# _rw_fpcheck_20261108.py — 重签结论撰写员独立指纹取证（本任务唯一写域内）
# 只读；hashlib 计算 sha256+bytes；python -I -X utf8 绝对路径运行。
import hashlib
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")

BASELINE = [
    ("out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py",
     "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508),
    ("lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py",
     "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759),
    ("lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff",
     "72b108021637cf7d225a9b109a542ec10c934abb1a8e40b8850a82c6bea9cdb9", 18454),
    ("lead/b2b_design_20261106/B2B_DESIGN.md",
     "565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf", 66735),
    ("lead/b2b_design_20261106/STATE_MATRIX.json",
     "1d4ccc937cfa78f1ac5144c15fd3e87152e45d41565bf5031bde53202667e016", 3558),
    ("lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md",
     "c7bcf035920234bdc66ec410564b296d4c18b62008dd5653ba76a26a38f10801", 28897),
    ("lead/n4_yi_final_20261108/B_EXECUTION_SPEC_V2_YI.md",
     "27f31bf560e9a71c5e9603d81a860233e7fc7b19e504eed4a15ea24a2077b067", 35486),
    ("lead/b2b_yi_supersede_20261108/YI_SUPERSEDE_JIA_BINDING.md",
     "255356ca789955cc2c084388f547a1435feb310f210617b988f761e7ff331c7b", 7344),
    ("lead/direction_ruling_20261108/RULING_DIRECTION.md",
     "0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653", 16514),
    ("lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md",
     "96071dd9d58e30a54966a2a1e16f4af918c2f8dd5825363510e8ced8bc6a8fea", 24661),
    ("lead/PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]

EXTRA = [
    ("lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md",
     "ee27b4caf4faa7920b602636bc0f43c1a265554fe6354659c59323fc11e3102e", 11948),
    ("lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md",
     "c364467d", 27225),
    ("lead/n4_yi_final_20261108/_n4v2_ast_rerun_out.txt",
     "9986fc2e", 22510),
    ("lead/bexec_n4_20261108/_n4_ast_scan_out.txt",
     "9986fc2e", 22510),
]

def digest(p: Path):
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)

ok = 0
total = 0
for rel, exp_sha, exp_bytes in BASELINE + EXTRA:
    p = ROOT / rel
    total += 1
    if not p.exists():
        print(f"MISSING | {rel}")
        continue
    sha, n = digest(p)
    if rel == "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md" or rel.endswith("_ast_scan_out.txt") or rel.endswith("_ast_rerun_out.txt"):
        m = ("MATCH" if sha.startswith(exp_sha) and n == exp_bytes else "MISMATCH")
    else:
        m = ("MATCH" if sha == exp_sha and n == exp_bytes else "MISMATCH")
    if m == "MATCH":
        ok += 1
    print(f"{m} | {rel} | sha256={sha} | bytes={n}")

print(f"TOTAL MATCH {ok}/{total}")
