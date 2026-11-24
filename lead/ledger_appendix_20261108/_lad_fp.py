# -*- coding: utf-8 -*-
# 入账草案撰写员：开工指纹自查（只读，不写任何台账）
import hashlib, os

def fp(path):
    if not os.path.exists(path):
        return "MISSING", 0, 0, 0
    with open(path, "rb") as f:
        b = f.read()
    h = hashlib.sha256(b).hexdigest()
    return h, len(b), len(b.splitlines()), len(b.split(b"\n"))

BASE = r"D:\Project\ra2-campaign-forge"
targets = [
    r"lead\PENDING_DECISIONS.md",
    r"lead\GOAL_THREE_TARGETS_20261018.md",
    r"lead\NEXT_STEPS_20261106.md",
    r"lead\n9_erratum_20261108\N9_SPEC_ERRATUM.md",
    r"lead\static_spec_n9_20261107\STATIC_COUNT_SPEC.md",
    r"lead\d_o1o4_necessity_20261108\O1_O4_NECESSITY.md",
    r"lead\slowframe_r3_20261108\S604_GAP_RECHECK.md",
    r"lead\b2b_yi_supersede_20261108\YI_SUPERSEDE_JIA_BINDING.md",
    r"lead\r2_final_grade_20261108\R2_FINAL_GRADE.md",
    r"lead\ledger_appendix_20261108\_la_draft1_n9_p6_erratum.md",
    r"lead\ledger_appendix_20261108\_la_draft2_o4_necessity.md",
    r"lead\ledger_appendix_20261108\_la_draft3_s604_gapdiff.md",
    r"lead\ledger_appendix_20261108\_la_draft4_yi_supersede_jia.md",
    r"lead\ledger_appendix_20261108\_la_SUMMARY.md",
    r"lead\ledger_appendix_20261108\_lv_subject_reply.txt",
    r"lead\ledger_appendix_20261108\_lv_er_pe_rerun_out.txt",
    r"lead\ledger_appendix_20261108\_lv_d14_recompute_out.txt",
    r"lead\ledger_appendix_20261108\_lv_r3_recompute_out.txt",
    r"lead\ledger_appendix_20261108\_la_er_pe_rerun_out.txt",
    r"lead\ledger_appendix_20261108\_la_d14_recompute_out.txt",
    r"lead\ledger_appendix_20261108\_la_r3_recompute_out.txt",
]
for t in targets:
    p = os.path.join(BASE, t)
    h, n, ls, ln = fp(p)
    print(f"{t}\n  sha256={h}\n  bytes={n} lines_splitlines={ls} lines_split_nl={ln}")
