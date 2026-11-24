# -*- coding: utf-8 -*-
"""_eiv_03_stats.py — 独立复核员 ③⑥⑦：一致率含义 / 额外信息量 / 置信度公式 /
有效独立层数，全部自己从只读 74 行 JSON 重算，并核对撰写人每个数字。

运行: python -I -X utf8 -B <绝对路径>
"""
import collections
import json
import math
import pathlib
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = ROOT / "lead" / "evidence_indep_20261109"
REG = ROOT / "lead" / "gate_pipeline_20261109" / "_gp_regression_out.json"


def h(p):
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p)) if 0 < p < 1 else 0.0


def mi(R, a, b, n):
    ca = collections.Counter(r[a] for r in R)
    cb = collections.Counter(r[b] for r in R)
    joint = collections.Counter((r[a], r[b]) for r in R)
    return sum((pxy := j / n) * math.log2(pxy / ((ca[x] / n) * (cb[y] / n)))
               for (x, y), j in joint.items() if j)


def cond_entropy(R, a, b, n):
    cb = collections.Counter(r[b] for r in R)
    joint = collections.Counter((r[a], r[b]) for r in R)
    out = 0.0
    for y, ny in cb.items():
        for x in ("CATCH", "PASS"):
            j = joint[(x, y)]
            if j:
                out -= (j / n) * math.log2((j / n) / (ny / n))
    return out


def main():
    O = json.loads(REG.read_text(encoding="utf-8"))
    R = O["rows"]
    n = len(R)
    out = {"n": n}

    # ---- ③ 一致率：交叉表 / φ / MI / 条件熵 ----
    ct = collections.Counter((r["r10"], r["n13"]) for r in R)
    ask_ct = {"PASS|CATCH": 16, "CATCH|CATCH": 20, "CATCH|PASS": 20, "PASS|PASS": 18}
    got_ct = {"%s|%s" % k: v for k, v in ct.items()}
    agree = ct[("CATCH", "CATCH")] + ct[("PASS", "PASS")]
    n11 = ct[("CATCH", "CATCH")]
    a = ct[("CATCH", "CATCH")] + ct[("CATCH", "PASS")]   # r10 CATCH
    b = ct[("CATCH", "CATCH")] + ct[("PASS", "CATCH")]   # n13 CATCH
    phi = (n11 * n - a * b) / math.sqrt(a * b * (n - a) * (n - b))
    MI = mi(R, "r10", "n13", n)
    H13 = h(b / n)
    H13g10 = cond_entropy(R, "n13", "r10", n)
    out["agreement"] = {
        "ask_cross_table": ask_ct, "recomputed": got_ct, "match": got_ct == ask_ct,
        "agree": agree, "rate": agree / n, "pct": 100 * agree / n,
        "phi": phi, "MI_bit": MI,
        "H_n13_bit": H13, "H_n13_given_r10_bit": H13g10,
        "H_residual_pct": 100 * H13g10 / H13,
        "both_CATCH": ct[("CATCH", "CATCH")],
        "both_CATCH_FP": sum(1 for r in R if r["r10"] == r["n13"] == "CATCH"
                             and r["expect"] == "PASS"),
        "both_PASS": ct[("PASS", "PASS")],
        "both_PASS_FN": sum(1 for r in R if r["r10"] == r["n13"] == "PASS"
                            and r["expect"] == "CATCH"),
        "both_PASS_FN_ids": [r["id"] for r in R if r["r10"] == r["n13"] == "PASS"
                             and r["expect"] == "CATCH"],
        "three_all_PASS_n": sum(1 for r in R if all(r[k] == "PASS"
                                                    for k in ("r10", "r12", "n13"))),
        "three_all_PASS_wrong": sum(1 for r in R if all(r[k] == "PASS"
                                                        for k in ("r10", "r12", "n13"))
                                    and r["expect"] == "CATCH"),
    }

    # ---- ③ 后验阶梯 / R12 增量信息 ----
    pi = sum(1 for r in R if r["expect"] == "CATCH") / n

    def cond(keys):
        sub = [r for r in R if all(r[k] == "PASS" for k in keys)]
        k = sum(1 for r in sub if r["expect"] == "CATCH")
        return len(sub), k, (k / len(sub) if sub else None)

    steps = {"prior": ([], pi), "n13": (["n13"], None),
             "n13+r10": (["n13", "r10"], None),
             "n13+r10+r12": (["n13", "r10", "r12"], None)}
    ladder = {}
    for k, (keys, _) in steps.items():
        if k == "prior":
            ladder[k] = {"n": n, "wrong": int(pi * n), "P": pi}
        else:
            N, kk, p = cond(keys)
            ladder[k] = {"n": N, "wrong": kk, "P": p}
    out["posterior_ladder"] = ladder
    out["R12_increment"] = {
        "P_after_n13_r10": ladder["n13+r10"]["P"],
        "P_after_n13_r10_r12": ladder["n13+r10+r12"]["P"],
        "identical": ladder["n13+r10"]["P"] == ladder["n13+r10+r12"]["P"],
        "log2_LR_bit": math.log2((ladder["n13+r10+r12"]["P"] / (1 - ladder["n13+r10+r12"]["P"]))
                                 / (ladder["n13+r10"]["P"] / (1 - ladder["n13+r10"]["P"]))),
        "P_r12_PASS_given_n13_PASS": sum(1 for r in R if r["n13"] == "PASS" and r["r12"] == "PASS")
                                      / sum(1 for r in R if r["n13"] == "PASS"),
    }

    # ---- ⑥ 置信度公式：假设 + 推导数值复核 ----
    q_n13 = sum(1 for r in R if r["expect"] == "CATCH" and r["n13"] == "PASS") / (pi * n)
    q_r10 = sum(1 for r in R if r["expect"] == "CATCH" and r["r10"] == "PASS") / (pi * n)
    c_n13 = sum(1 for r in R if r["expect"] == "PASS" and r["n13"] == "PASS") / ((1 - pi) * n)
    c_r10 = sum(1 for r in R if r["expect"] == "PASS" and r["r10"] == "PASS") / ((1 - pi) * n)
    # formula_posterior: P(E|all PASS) = pi*prod q / [pi*prod q + (1-pi)*prod c]
    num = pi * q_r10 * q_n13
    den = num + (1 - pi) * c_r10 * c_n13
    post2_indep = num / den
    joint_miss_indep = q_r10 * q_n13
    obs_joint_miss = sum(1 for r in R if r["expect"] == "CATCH" and r["r10"] == "PASS"
                         and r["n13"] == "PASS") / (pi * n)
    # Wilson 95% CI for q_n13 (n=39 CATCH rows, k=3 missed by n13)
    k = sum(1 for r in R if r["expect"] == "CATCH" and r["n13"] == "PASS")
    nn = sum(1 for r in R if r["expect"] == "CATCH")   # exact integer count, avoid int(pi*n) float truncation
    z = 1.96
    denw = 1 + z * z / nn
    centre = (k / nn + z * z / (2 * nn)) / denw
    half = z * math.sqrt(k / nn * (1 - k / nn) / nn + z * z / (4 * nn * nn)) / denw
    out["confidence_formula"] = {
        "pi": pi, "q_n13": q_n13, "q_r10": q_r10,
        "c_n13_specificity": c_n13, "c_r10_specificity": c_r10,
        "numerator_pi_prod_q": num, "denominator": den,
        "posterior_2_indep_layers_recomputed": post2_indep,
        "writer_posterior": 0.0887850467289718,
        "posterior_match": abs(post2_indep - 0.0887850467289718) < 1e-12,
        "joint_miss_indep_product": joint_miss_indep,
        "writer_indep_bound": 0.037475345167652864,
        "joint_miss_match": abs(joint_miss_indep - 0.037475345167652864) < 1e-12,
        "observed_joint_miss": obs_joint_miss,
        "observed_over_indep": obs_joint_miss / joint_miss_indep,
        "wilson95_q_n13": [centre - half, centre + half],
        "writer_wilson95": [0.026506914073495688, 0.2032137312805527],
        "frechet_upper_bound_min_q": min(q_r10, q_n13),
        "note_on_mislabel": "0.0375 是独立假设下的联合漏报期望，不是上界；"
                            "分布无关上界是 min(q_i)=3/39=0.0769（撰写人在 "
                            "d_correlation_correction 里另给了 Fréchet 上界，未混用）",
    }

    # ---- ⑥ 90% 一致框架算术复核 ----
    rho = 0.90
    h_rho = h(rho)
    out["framework_90"] = {
        "H2_given_1_bit": h_rho,
        "I_redundant_bit": 1 - h_rho,
        "independent_new_bit": 1.0,
        "surviving_pct": 100 * h_rho,
        "rho_eff": (rho - 0.5) / 0.5,
        "n_eff_design_effect": 2 / (1 + (rho - 0.5) / 0.5),
        "LR2_bit": math.log2(9),
        "discounted_LR2_bit": (1 - (rho - 0.5) / 0.5) * math.log2(9),
        "assumption_check": "H(C2|C1)=H(rho) 仅在 P(C2!=C1|C1=PASS)=P(C2!=C1|C1=CATCH)=1-rho "
                            "且 H(C2)=1 时成立；label 一致率≠误差相关，"
                            "两个独立且各 95% 准确的分类器也可有 ~90.5% 标签一致",
    }

    # ---- ⑦ 折算层数：把撰写人给的多个 k_eff 全部重算 ----
    def odds(p):
        return p / (1 - p)
    p1, p3 = ladder["n13"]["P"], ladder["n13+r10+r12"]["P"]
    k_odds = math.log(odds(p3) / odds(pi)) / math.log(odds(p1) / odds(pi))
    k_prob_upstream = math.log(p3 / pi) / math.log(p1 / pi)
    info_ratio = (pi - p3) / (pi - p1)
    out["layer_count"] = {
        "k_from_posterior_odds": k_odds, "writer": 0.6697,
        "k_upstream_prob_ratio_0.61": k_prob_upstream, "writer_upstream": 0.61,
        "info_gain_ratio_0.804": info_ratio, "writer": 0.8042,
        "n_eff_equicorr_0.9": 2 / (1 + 0.9),
        "final_answer_writer": "1 层（保守）／0.61 层（按后验信息量折算）；绝不可按 3 层",
        "numeric_field": 1,
        "n_distinct_k_eff_definitions": 3,
        "structural_max_independent_roots": 1,
        "why": "依赖图 R10 -> {R12, N13.C}；R12=f(R10) 确定性子集，N13.C=g(R10.kind)，"
               "共用 extract_spans 与 55/74 行同一 tokens ⇒ 独立证据根只有 1 个",
    }

    # ---- 留出集误差相关双检是否真跑 ----
    H = json.loads((ROOT / "lead" / "chain_vs_single_20261109" / "_cs_holdout_out.json")
                   .read_text(encoding="utf-8"))["unseen"]
    # 20 条：是否有逐字重复（与 74 行语料比对）
    reg_texts = set()
    for r in R:
        reg_texts.add(r["text_head"][:38])
    dup = [x["id"] for x in H if x["text"][:38] in reg_texts]
    # 20 条上 r10/n13 误差相关（只有 expect + n13/chain/v12，没有 r10 列 → 无法算两两误差相关）
    out["holdout_check"] = {
        "n": len(H),
        "has_r10_column": any("r10" in x for x in H),
        "has_n13_column": any("n13" in x for x in H),
        "duplicate_ids_by_head": dup,
        "can_compute_pairwise_error_corr": False,
        "reason": "_cs_holdout_out.json 每行只有 id/expect/n13/chain/v12/note/text，"
                  "缺 r10 与 r12 列，无法在其上算 corr(1{err_i},1{err_j})；"
                  "该双检在撰写人回件里是『估计方法②』(设计)，不是实跑结果",
    }

    (W / "_eiv_03_stats_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- 控制台 ----
    print("== ③ 一致率 / 额外信息量 ==")
    A = out["agreement"]
    print("  cross_table =", A["recomputed"], "match_ask =", A["match"])
    print("  agree = %d/%d = %.3f%%  phi = %.6f  MI = %.6f bit" %
          (A["agree"], n, A["pct"], A["phi"], A["MI_bit"]))
    print("  H(N13|R10) = %.6f / H(N13) = %.6f = %.2f%%" %
          (A["H_n13_given_r10_bit"], A["H_n13_bit"], A["H_residual_pct"]))
    print("  both_CATCH=%d (FP=%d)  both_PASS=%d (FN=%d %s)  三层全PASS=%d 错=%d" %
          (A["both_CATCH"], A["both_CATCH_FP"], A["both_PASS"], A["both_PASS_FN"],
           A["both_PASS_FN_ids"], A["three_all_PASS_n"], A["three_all_PASS_wrong"]))
    print("== ③ 后验阶梯 / R12 增量 ==")
    for k, v in out["posterior_ladder"].items():
        print("  %-18s n=%-3d wrong=%-2d P(CATCH|cond)=%s" %
              (k, v["n"], v["wrong"], ("%.4f" % v["P"]) if v["P"] is not None else "-"))
    print("  R12 increment: identical=%s log2LR=%.6f bit  P(r12PASS|n13PASS)=%.4f" %
          (out["R12_increment"]["identical"], out["R12_increment"]["log2_LR_bit"],
           out["R12_increment"]["P_r12_PASS_given_n13_PASS"]))
    print("== ⑥ 置信度公式推导复核 ==")
    C = out["confidence_formula"]
    print("  pi=%.4f q_n13=%.6f q_r10=%.6f c_n13=%.4f c_r10=%.4f" %
          (C["pi"], C["q_n13"], C["q_r10"], C["c_n13_specificity"], C["c_r10_specificity"]))
    print("  P(E|2独立层全PASS) = %.16f  writer=%.16f  match=%s" %
          (C["posterior_2_indep_layers_recomputed"], C["writer_posterior"], C["posterior_match"]))
    print("  joint_miss_indep = %.16f  match=%s  observed=%.6f  ratio=%.4f" %
          (C["joint_miss_indep_product"], C["joint_miss_match"],
           C["observed_joint_miss"], C["observed_over_indep"]))
    print("  Wilson95 =", ["%.6f" % x for x in C["wilson95_q_n13"]],
          "writer =", ["%.6f" % x for x in C["writer_wilson95"]])
    print("  Fréchet 分布无关上界 min q_i = %.6f" % C["frechet_upper_bound_min_q"])
    print("== ⑥ 90% 框架 ==")
    F = out["framework_90"]
    print("  H(C2|C1)=%.4f bit new / I=%.4f redundant / rho_eff=%.2f / n_eff=%.4f" %
          (F["H2_given_1_bit"], F["I_redundant_bit"], F["rho_eff"], F["n_eff_design_effect"]))
    print("  LR2=%.4f bit -> discounted %.4f bit" % (F["LR2_bit"], F["discounted_LR2_bit"]))
    print("== ⑦ 折算层数 ==")
    L = out["layer_count"]
    print("  k(后验几率)=%.4f  k(上游概率比)=%.4f  info_gain_ratio=%.4f  n_eff(rho=.9)=%.4f" %
          (L["k_from_posterior_odds"], L["k_upstream_prob_ratio_0.61"],
           L["info_gain_ratio_0.804"], L["n_eff_equicorr_0.9"]))
    print("  distinct k_eff definitions =", L["n_distinct_k_eff_definitions"],
          "| 独立证据根 =", L["structural_max_independent_roots"],
          "| numeric field =", L["numeric_field"])
    print("== 留出集误差相关双检 ==")
    print(" ", out["holdout_check"])
    print("written: _eiv_03_stats_out.json")


if __name__ == "__main__":
    main()
