# -*- coding: utf-8 -*-
"""_ei_07_final.py — effective independent layer count, classification of the
three existing layers, and the discount factor for "multi-layer agreement".

Uses the 74-row read-only regression JSON and the ask-supplied cross table.
python -I -X utf8 -B <abs path>
"""
import collections
import json
import math
import pathlib
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = ROOT / "lead" / "evidence_indep_20261109"
O = json.loads((ROOT / "lead" / "gate_pipeline_20261109" / "_gp_regression_out.json")
               .read_text(encoding="utf-8"))
R = O["rows"]
n = len(R)
pi = sum(1 for r in R if r["expect"] == "CATCH") / n


def cond(keys):
    sub = [r for r in R if all(r[k] == "PASS" for k in keys)]
    k = sum(1 for r in sub if r["expect"] == "CATCH")
    return {"n": len(sub), "wrong": k, "P(CATCH|all_PASS)": k / len(sub) if sub else None,
            "wrong_ids": [r["id"] for r in sub if r["expect"] == "CATCH"]}


steps = [("prior", []), ("n13", ["n13"]),
         ("n13+r10", ["n13", "r10"]),
         ("n13+r10+r12", ["n13", "r10", "r12"])]
res = {"prior_P_CATCH": pi, "steps": {k: cond(v) for k, v in steps}}

# k_eff: if k independent layers each with the single-layer likelihood ratio
# LR = P(PASS|E)/P(PASS|not E), then posterior odds = prior odds * LR^k.
# Solve for k from observed posterior odds after 3 layers vs after 1 layer.
def odds(p):
    return p / (1 - p)
p1 = res["steps"]["n13"]["P(CATCH|all_PASS)"]
p3 = res["steps"]["n13+r10+r12"]["P(CATCH|all_PASS)"]
# single-layer LR in log-odds units
lr1_log = math.log(odds(p1) / odds(pi))
k_from_posterior = math.log(odds(p3) / odds(pi)) / lr1_log
# alternative: information-gain ratio (used upstream _cs_info_out.txt:9)
info1 = pi - p1
info3 = pi - p3
res["k_eff"] = {
    "single_layer_log_LR": lr1_log,
    "k_from_posterior_odds": k_from_posterior,
    "info_gain_1_layer": info1, "info_gain_3_layers": info3,
    "info_gain_ratio": info3 / info1,
    "upstream_report_k_eff": 0.61,
    "upstream_source": "lead/chain_vs_single_20261109/CHAIN_VS_SINGLE.md:206, "
                       "lead/chain_vs_single_20261109/_cs_info_out.txt:9",
    "R12_incremental_info_bit": 0.0,
    "R12_incremental_evidence": "P(CATCH|n13+r10)=%.4f == P(CATCH|n13+r10+r12)=%.4f" % (
        res["steps"]["n13+r10"]["P(CATCH|all_PASS)"],
        res["steps"]["n13+r10+r12"]["P(CATCH|all_PASS)"]),
}
# R10 x N13 agreement restricted to the 'all PASS' region and to C-only rows
sub = [r for r in R if r["n13"] == "PASS"]
res["conditional_agreement"] = {
    "n13_PASS_n": len(sub),
    "P(r10=PASS|n13=PASS)": sum(1 for r in sub if r["r10"] == "PASS") / len(sub),
    "P(r12=PASS|n13=PASS)": sum(1 for r in sub if r["r12"] == "PASS") / len(sub),
    "three_all_PASS_n": len([r for r in R if all(r[k] == "PASS" for k in ("r10", "r12", "n13"))]),
    "three_all_PASS_wrong": 3,
    "three_all_PASS_wrong_ids": ["GP-A1", "GP-A2", "GP-A3"],
    "three_all_PASS_error_pct": 100 * 3 / 18,
}
# token contract overlap
c = collections.Counter(tuple(r["tokens"]) for r in R)
res["token_contract"] = {
    "families": [{"tokens": list(k), "rows": v} for k, v in c.items()],
    "identical_to_N13_DEFAULT_TOKENS_rows": c[("已入账", "已追加", "已生效")],
    "pct": 100 * c[("已入账", "已追加", "已生效")] / n,
}
# classification (step 5a)
res["classification"] = {
    "R10": "部分独立（相对 V1V2 独立；相对 N13/R12 为上游，被转发/复用）",
    "R12": "不独立（_g7_predicates.py:144 调用 r10_context，与 R10 同模块同函数）",
    "N13": "部分独立（A/B 微段判据 _seg_bounds/_A_AFTER 自带局部证据，但 C 类在 :253-256 转发 R10 kind，12 类在 :242-243 消费 R12 命中）",
    "R9/R11": "独立（_g7_predicates.py:55-65 / :157-222，要素在场与 hashlib 引用锚回验，与断言层正交；但未计入本次 74 行判定）",
    "V1V2": "相对 R10/R12 代码级独立（_ei_05_admission.py A1/A2/A3/A4 全 PASS）；相对 N13 不通过 A2（共享字面 '已入账'）",
}
res["discount"] = {
    "current_three_layer_agreement_should_count_as": "1 层（保守）／0.61 层（按后验信息量折算）；绝不可按 3 层",
    "numeric": 1,
    "posterior_k_eff": k_from_posterior,
    "reason": "R12 增量信息 0 bit；N13.C 转发 R10；55/74 行共用同一三词词表；"
              "三层全 PASS 时实测条件错误率 3/18=16.7%，独立假设下应为 "
              "q_r10*q_n13=0.0375（2.6 倍乐观）。",
}
# what this work cannot decide
res["cannot_decide"] = [
    "真机上 gamemd.exe / ra2loader / YURI.exe 的运行态（铁律零真机，未验）",
    "生产语料上的真实 q_i / ρ：74 行是 train=test 且含定向构造的对抗样本，非盲留出集",
    "V1V2 在 spans>0 区域的语义判定正确性：本次只按字面 V2_OVERRIDE 词族 + 三词做 span 扫描，未做人工语义标注",
    "Cohen's κ / 双盲人工标注一致性（未做）",
    "第五层（同行评审/另一套语料/结构回验）的实际增益：无留盘数据，未验",
    "改谓词后的效果：本任务不改任何谓词模块与语料，所有方案均为设计，未实装",
]
(W / "_ei_07_final_out.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False, indent=1))
