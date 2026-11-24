# -*- coding: utf-8 -*-
"""_g9_regression.py — _g9_gate.py 全历史回归运行器（只读扫描，写仅落本写域）。

语料 = 任务书清点的前 30 件历史交付件（按清点原序取前 30，见 _g9_regression.md §2）。
统一清单（回归口径，两清单均为本会话既有门禁纪律的实措）：
  required_elements = ["被核对象", "SHA256", "字节数"]   —— 复核回件绑定行三要素（本任务书铁律原文）
  forbidden_words   = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]
                      —— 探针 BAD_BAN 越权词族（GATE_FALSE_POSITIVE_5_6_7.md:40 逐字）

附录 A：g7 轮 TV 违规样本 8 件 + 真实件 4 件（门禁原判语境清单），验「不放松」：
  TV 清单 req=["APPROVE_SCOPE"]（旧门禁实词表，_gv_gates/1552e9fe.py:9 同款）；
  真实件清单 req=["被核对象","SHA256","字节数"]（四件均含绑定行），另对 CANDIDATE 附加 APPROVE_SCOPE 口径一趟。
运行：python -I -X utf8 _g9_regression.py → _g9_regression_out.json + 控制台摘要表。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _g9_gate import check_deliverable, self_test, REPO_ROOT  # noqa: E402

OUT_JSON = Path(__file__).parent / "_g9_regression_out.json"

# 任务书清点（lead/ depth≤1、3000B<size<200KB 的 .md，共 334 件）原序前 30 件
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

REQ_BIND = ["被核对象", "SHA256", "字节数"]
FORB_BAD_BAN = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]

TV_FIXTURES = [
    "lead/gate_fp7_20261108/_g7_tv1_missing_element.md",
    "lead/gate_fp7_20261108/_g7_tv2_overreach_positive.md",
    "lead/gate_fp7_20261108/_g7_tv3_double_negation.md",
    "lead/gate_fp7_20261108/_g7_tv4_no_binding.md",
    "lead/gate_fp7_20261108/_g7_tv5_forged_binding.md",
    "lead/gate_fp7_20261108/_g7_tv6_binding_missing_obj.md",
    "lead/gate_fp7_20261108/_g7_tv7_split_token.md",
    "lead/gate_fp7_20261108/_g7_tv7b_wrapper_only.md",
]
REAL_FOUR = [
    "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md",
    "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
    "lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md",
    "lead/c97_scope_recheck_20261108/C97_SCOPE_RECHECK.md",
]


def evidence_lines(text, needle, limit=6):
    """取含 needle 的行（带行号），供逐件人工判真伪。"""
    out = []
    for i, line in enumerate(text.split("\n"), 1):
        if needle in line:
            out.append({"line": i, "text": line.strip()[:200]})
            if len(out) >= limit:
                break
    return out


def run_one(rel, req, forb):
    p = REPO_ROOT / rel
    r = check_deliverable(p, req, forb)
    r["rel"] = rel
    # 给「缺绑定行」类问题附证据行（被核对象出现处），供逐件判定真伪
    if any(x["msg"].startswith("缺 SHA256 绑定行") for x in r["problems"]):
        text = p.read_bytes().decode("utf-8", errors="replace")
        r["evidence_被核对象_lines"] = evidence_lines(text, "被核对象")
    return r


def main():
    checks, st_ok = self_test()
    print("== 自检 all_pass =", st_ok)
    for c in checks:
        print("   ", c)

    results_30 = [run_one(rel, REQ_BIND, FORB_BAD_BAN) for rel in DOCS_30]

    # 附录 A：TV 违规样本（旧门禁实词表口径）
    results_tv = [run_one(rel, ["APPROVE_SCOPE"], FORB_BAD_BAN) for rel in TV_FIXTURES]
    # 附录 B：四真实件（绑定要素口径）
    results_real = [run_one(rel, REQ_BIND, FORB_BAD_BAN) for rel in REAL_FOUR]
    # 附录 B2：CANDIDATE 附加旧门禁词表口径（APPROVE_SCOPE）
    results_real.append(run_one(REAL_FOUR[0], ["APPROVE_SCOPE"], FORB_BAD_BAN))

    payload = {
        "generated_by": "_g9_regression.py",
        "checklist": {"required_elements": REQ_BIND, "forbidden_words": FORB_BAD_BAN,
                      "source": "绑定行三要素=本任务书铁律；禁用词=BAD_BAN 探针族（GATE_FALSE_POSITIVE_5_6_7.md:40）"},
        "corpus_selection": "任务书清点 334 件原序前 30 件",
        "self_test": checks, "self_test_all_pass": st_ok,
        "results_30": results_30,
        "appendix_tv": results_tv,
        "appendix_real4": results_real,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written:", OUT_JSON)

    def brief(tag, rs):
        print("---- %s ----" % tag)
        for r in rs:
            pv = "/".join("%s:%s" % (k, r["predicates"][k]["verdict"][:4]) for k in ("R9", "R10", "R12", "R11"))
            npro = len(r["problems"])
            nold = len(r.get("old_gate", {}).get("problems", []))
            print("%-72s %7dB gate=%s %s | newProblems=%d oldProblems=%d"
                  % (r["rel"], r["bytes"], r["verdict"], pv, npro, nold))

    brief("30 件历史回归", results_30)
    brief("附录A TV 违规样本", results_tv)
    brief("附录B 四真实件(+CANDIDATE旧词表)", results_real)


if __name__ == "__main__":
    main()
