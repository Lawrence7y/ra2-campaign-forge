# -*- coding: utf-8 -*-
# _g9v_subset.py — 复核 ⑤：30 件上「新 problems ⊆ 旧门禁 problems」独立归一化比对；
# 找出 新增（旧无新有）与 消除（旧有新无），核对撰写人「仅 _integ 消除 1 条、仅 b_unclosed_trace 新增 1 条」。
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from _g9_gate import check_deliverable, REPO_ROOT  # noqa: E402

DOCS_30 = [
    "lead/GOAL3T_CRITERIA_STATUS_20261021.md",
    "lead/GOAL3T_e4_VERIFY_20261026.md",
    "lead/PENDING_DECISIONS.md",
    "lead/a_dim_reduced_20261108/A_REDUCED_FORM.md",
    "lead/a_residual_20261106/A_RESIDUAL_REFERENCES.md",
    "lead/a_residual_20261106/TASK.md",
    "lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md",
    "lead/b2b_candidate_20261106/TASK.md",
    "lead/b2b_candidate_20261106/TESTS_REPORT.md",
    "lead/b2b_candidate_lf_20261107/N1_CLOSURE.md",
    "lead/b2b_candidate_review2_20261106/CANDIDATE_SEMANTIC_REVIEW_R2.md",
    "lead/b2b_candidate_review2_20261106/TASK.md",
    "lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md",
    "lead/b2b_candidate_review_20261106/CANDIDATE_SEMANTIC_REVIEW.md",
    "lead/b2b_candidate_review_20261106/TASK.md",
    "lead/b2b_design_20261106/B2B_DESIGN.md",
    "lead/b2b_design_20261106/TASK.md",
    "lead/b2b_design_20261106/_draft_semantics.md",
    "lead/b2b_design_20261106/_hunks_frag.md",
    "lead/b2b_isolated_20261107/INTEGRATION_REPORT.md",
    "lead/b2b_isolated_20261107/_integ_INTEGRATION_REPORT.md",
    "lead/b2b_n1_binding_20261107/N1_BINDING.md",
    "lead/b2b_preaudit_20261106/B2B_PREAUDIT.md",
    "lead/b2b_preaudit_20261106/TASK.md",
    "lead/b2b_yi_supersede_20261108/YI_SUPERSEDE_JIA_BINDING.md",
    "lead/b2_preaudit_20261106/B2_PREAUDIT.md",
    "lead/b2_preaudit_20261106/TASK.md",
    "lead/bexec_n4_20261108/B_EXECUTION_SPEC.md",
    "lead/bexec_n4_20261108/_n4_SPEC_N4_B2B_MATRIX.md",
    "lead/b_unclosed_trace_20261108/B_BREAKPOINT2_TRACE.md",
]
REQ = ["被核对象", "SHA256", "字节数"]
FORB = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]

PAREN = re.compile(r"（[^）]*）$")

def norm(msg):
    """归一化：剥尾部全角括注；朴素越权计数条 → token 级。"""
    m = re.match(r"越权断言 (.+?)（朴素字面计数", msg)
    if m:
        return "越权断言 " + m.group(1)
    return PAREN.sub("", msg)

rows = []
for rel in DOCS_30:
    r = check_deliverable(REPO_ROOT / rel, REQ, FORB)
    new = {norm(x["msg"]) for x in r["problems"]}
    old = {norm(x) for x in r["old_gate"]["problems"]}
    added = sorted(new - old)      # 新增：新模块独有的 problem
    removed = sorted(old - new)    # 消除：旧门禁有而新门禁无
    rows.append({"rel": rel, "n_new": len(r["problems"]), "n_old": len(r["old_gate"]["problems"]),
                 "added": added, "removed": removed})

adds = [x for x in rows if x["added"]]
rems = [x for x in rows if x["removed"]]
print("items_with_added:", len(adds))
for x in adds:
    print("  ADD", x["rel"], x["added"])
print("items_with_removed:", len(rems))
for x in rems:
    print("  REM", x["rel"], x["removed"])
(HERE / "_g9v_subset_out.json").write_text(
    json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
