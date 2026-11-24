# -*- coding: utf-8 -*-
# _g9v_regress.py — 复核员独立复跑：全语料重跑（30+TV8+真实件4+附加1），与 _g9_regression_out.json 程序化比对。
# 只读扫描；写仅落本写域本文件旁 _g9v_regress_out.json。谓词一律复用 _g7_predicates（经 _g9_gate 加载）。
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from _g9_gate import check_deliverable, REPO_ROOT  # noqa: E402

OUT = HERE / "_g9v_regress_out.json"
THEIRS = HERE / "_g9_regression_out.json"

# 清单直接取自回归运行器声明口径（_g9_regression.py:59-60 逐字）
REQ_BIND = ["被核对象", "SHA256", "字节数"]
FORB_BAD_BAN = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]
TV_REQ = ["APPROVE_SCOPE"]

# 30 件清单：从撰写人的 _g9_regression.py 逐字复制（:26-57）——语料选择本身是待核项，先按同语料复跑
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
TV8 = [
    "lead/gate_fp7_20261108/_g7_tv1_missing_element.md",
    "lead/gate_fp7_20261108/_g7_tv2_overreach_positive.md",
    "lead/gate_fp7_20261108/_g7_tv3_double_negation.md",
    "lead/gate_fp7_20261108/_g7_tv4_no_binding.md",
    "lead/gate_fp7_20261108/_g7_tv5_forged_binding.md",
    "lead/gate_fp7_20261108/_g7_tv6_binding_missing_obj.md",
    "lead/gate_fp7_20261108/_g7_tv7_split_token.md",
    "lead/gate_fp7_20261108/_g7_tv7b_wrapper_only.md",
]
REAL4 = [
    "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md",
    "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
    "lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md",
    "lead/c97_scope_recheck_20261108/C97_SCOPE_RECHECK.md",
]

def run(rel, req, forb):
    return check_deliverable(REPO_ROOT / rel, req, forb)

def key(r):
    return (r["rel"], tuple(r["checklist"]["required_elements"]),
            tuple(r["checklist"]["forbidden_words"]))

def slim(r):
    return {
        "verdict": r["verdict"],
        "pv": {k: r["predicates"][k]["verdict"] for k in ("R9", "R10", "R12", "R11")},
        "problems": [x["msg"] for x in r["problems"]],
        "nwarn": len(r["warnings"]),
        "bytes": r["bytes"], "sha256": r["sha256"],
        "r10_kinds": r["predicates"]["R10"]["kinds"],
        "r11": {"bindings": r["predicates"]["R11"]["bindings"],
                "reverified": r["predicates"]["R11"]["reverified"],
                "match_true": r["predicates"]["R11"]["match_true"],
                "paths": [b.get("path") for b in r["predicates"]["R11"]["binding_details"]]},
    }

def main():
    mine = []
    tags = []
    for rel in DOCS_30:
        r = run(rel, REQ_BIND, FORB_BAD_BAN); r["rel"] = rel; mine.append(r); tags.append("D30")
    for rel in TV8:
        r = run(rel, TV_REQ, FORB_BAD_BAN); r["rel"] = rel; mine.append(r); tags.append("TV")
    for rel in REAL4:
        r = run(rel, REQ_BIND, FORB_BAD_BAN); r["rel"] = rel; mine.append(r); tags.append("REAL")
    r = run(REAL4[0], TV_REQ, FORB_BAD_BAN); r["rel"] = REAL4[0]; mine.append(r); tags.append("REAL-ALT")

    mine_map = {key(r): slim(r) for r in mine}

    theirs = json.loads(THEIRS.read_text(encoding="utf-8"))
    theirs_map = {}
    for block in ("results_30", "appendix_tv", "appendix_real4"):
        for r in theirs[block]:
            theirs_map[key(r)] = slim(r)

    diffs = []
    for k, v in mine_map.items():
        if k not in theirs_map:
            diffs.append({"key": list(k), "issue": "absent_in_theirs"})
            continue
        t = theirs_map[k]
        for f in ("verdict", "pv", "problems", "nwarn", "bytes", "sha256", "r10_kinds", "r11"):
            if json.dumps(v[f], sort_keys=True, ensure_ascii=False) != json.dumps(t[f], sort_keys=True, ensure_ascii=False):
                diffs.append({"key": list(k), "field": f, "mine": v[f], "theirs": t[f]})

    # 聚合统计（F2 覆盖缺口核验）
    agg = {"d30_total": 0, "d30_clean": [], "d30_problems": {}, "d30_bindings": 0,
           "d30_path_null": 0, "d30_reverified": 0, "d30_match_true": 0,
           "d30_r10_assertion_total": 0, "d30_r12_hits_total": 0}
    for r, tg in zip(mine, tags):
        if tg != "D30":
            continue
        agg["d30_total"] += 1
        if not r["problems"]:
            agg["d30_clean"].append(r["rel"])
        else:
            agg["d30_problems"][r["rel"]] = [x["msg"][:90] for x in r["problems"]]
        p11 = r["predicates"]["R11"]
        agg["d30_bindings"] += p11["bindings"]
        agg["d30_path_null"] += sum(1 for b in p11["binding_details"] if not b.get("path"))
        agg["d30_reverified"] += p11["reverified"]
        agg["d30_match_true"] += p11["match_true"]
        agg["d30_r10_assertion_total"] += r["predicates"]["R10"]["kinds"]["assertion"]
        agg["d30_r12_hits_total"] += r["predicates"]["R12"]["double_neg_hits"]

    tv_verdicts = {r["rel"].split("/")[-1]: r["verdict"] for r, tg in zip(mine, tags) if tg == "TV"}
    real_verdicts = {}
    for r, tg in zip(mine, tags):
        if tg in ("REAL", "REAL-ALT"):
            real_verdicts[r["rel"].split("/")[-1] + "|" + ",".join(r["checklist"]["required_elements"])] = {
                "verdict": r["verdict"],
                "r10_kinds": r["predicates"]["R10"]["kinds"],
                "r12": r["predicates"]["R12"]["double_neg_hits"],
                "r11_match": r["predicates"]["R11"]["match_true"],
                "nprob": len(r["problems"])}

    payload = {"generated_by": "_g9v_regress.py（复核员独立复跑）",
               "n_mine": len(mine), "n_theirs": len(theirs_map),
               "n_diff": len(diffs), "diffs": diffs,
               "agg_d30": agg, "tv_verdicts": tv_verdicts, "real_verdicts": real_verdicts,
               "results": [{k: v for k, v in slim(r).items()} for r in mine]}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    print("n_mine=%d n_theirs=%d n_diff=%d" % (len(mine), len(theirs_map), len(diffs)))
    for d in diffs:
        print("DIFF:", json.dumps(d, ensure_ascii=False)[:400])
    print("AGG_D30:", json.dumps(agg, ensure_ascii=False, indent=1))
    print("TV:", json.dumps(tv_verdicts, ensure_ascii=False))
    print("REAL:", json.dumps(real_verdicts, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
