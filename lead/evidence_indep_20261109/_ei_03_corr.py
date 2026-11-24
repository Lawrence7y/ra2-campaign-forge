# -*- coding: utf-8 -*-
"""_ei_03_corr.py — quantify R10 x N13 dependence on the 74-row corpus, and
give the conditional / information-theoretic extra-information framework.

Sources (read-only, fingerprints verified in _ei_00_setup_out.json):
  lead/gate_pipeline_20261109/_gp_regression_out.json  (74 rows, r10/n13/r12/chain/expect)
  ask-supplied cross table (verified by recomputation below)

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
REG = ROOT / "lead" / "gate_pipeline_20261109" / "_gp_regression_out.json"


def mi(R, a, b, n):
    ca, cb = collections.Counter(r[a] for r in R), collections.Counter(r[b] for r in R)
    joint = collections.Counter((r[a], r[b]) for r in R)
    v = 0.0
    for x, nx in ca.items():
        for y, ny in cb.items():
            pxy = joint[(x, y)] / n
            if pxy:
                v += pxy * math.log2(pxy / ((nx / n) * (ny / n)))
    return v


def h(p):
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p)) if 0 < p < 1 else 0.0


def cond_entropy(R, a, b, n):
    """H(A|B) for binary labels."""
    cb = collections.Counter(r[b] for r in R)
    joint = collections.Counter((r[a], r[b]) for r in R)
    out = 0.0
    for y, ny in cb.items():
        for x in ("CATCH", "PASS"):
            pxy = joint[(x, y)] / n
            if pxy:
                out -= pxy * math.log2(pxy / (ny / n))
    return out


def main():
    O = json.loads(REG.read_text(encoding="utf-8"))
    R = O["rows"]
    n = len(R)
    assert n == 74 and O["corpus_n"] == 74
    ct = collections.Counter((r["r10"], r["n13"]) for r in R)
    ask_ct = {"PASS|CATCH": 16, "CATCH|CATCH": 20, "CATCH|PASS": 20, "PASS|PASS": 18}
    got_ct = {"%s|%s" % k: v for k, v in ct.items()}
    res = {"n": n, "ask_cross_table": ask_ct, "recomputed_cross_table": got_ct,
           "cross_table_match": got_ct == ask_ct}

    agree = ct[("CATCH", "CATCH")] + ct[("PASS", "PASS")]
    disagree = ct[("CATCH", "PASS")] + ct[("PASS", "CATCH")]
    # Pearson phi on CATCH=1
    a = ct[("CATCH", "CATCH")] + ct[("CATCH", "PASS")]  # r10 CATCH
    b = ct[("CATCH", "CATCH")] + ct[("PASS", "CATCH")]  # n13 CATCH
    n11 = ct[("CATCH", "CATCH")]
    phi_num = n11 * n - a * b
    phi_den = math.sqrt(a * b * (n - a) * (n - b))
    phi = phi_num / phi_den if phi_den else 0.0
    # conditional P(n13=CATCH | r10=CATCH) vs marginal
    p_n13_catch = b / n
    p_n13_catch_given_r10_catch = n11 / a
    p_n13_pass_given_r10_pass = ct[("PASS", "PASS")] / (n - a)
    # mutual information & conditional entropy
    MI = mi(R, "r10", "n13", n)
    H_n13 = h(p_n13_catch)
    H_n13_given_r10 = cond_entropy(R, "n13", "r10", n)
    res["agreement"] = {
        "agree": agree, "disagree": disagree, "rate": agree / n,
        "pct": 100.0 * agree / n, "phi": phi, "phi_pct": 100.0 * phi,
        "P(n13=CATCH)": p_n13_catch,
        "P(n13=CATCH|r10=CATCH)": p_n13_catch_given_r10_catch,
        "P(n13=PASS|r10=PASS)": p_n13_pass_given_r10_pass,
        "MI_r10_n13_bit": MI, "H_n13_bit": H_n13,
        "H_n13_given_r10_bit": H_n13_given_r10,
        "residual_info_pct": 100.0 * (H_n13 - MI) / H_n13 if H_n13 else None,
    }

    # (b) what the agreement means in this corpus
    exp_ct = collections.Counter((r["r10"], r["n13"], r["expect"]) for r in R)
    both_catch = [r for r in R if r["r10"] == "CATCH" and r["n13"] == "CATCH"]
    both_pass = [r for r in R if r["r10"] == "PASS" and r["n13"] == "PASS"]
    res["agreement_meaning"] = {
        "both_CATCH": len(both_catch),
        "both_CATCH_true": sum(1 for r in both_catch if r["expect"] == "CATCH"),
        "both_CATCH_false_positive": sum(1 for r in both_catch if r["expect"] == "PASS"),
        "both_PASS": len(both_pass),
        "both_PASS_true": sum(1 for r in both_pass if r["expect"] == "PASS"),
        "both_PASS_false_negative": sum(1 for r in both_pass if r["expect"] == "CATCH"),
        "both_PASS_false_negative_ids": [r["id"] for r in both_pass if r["expect"] == "CATCH"],
        "conflict_rows": [(r["id"], r["r10"], r["n13"], r["expect"]) for r in R
                          if r["r10"] != r["n13"]][:6],
        "n_disagree": disagree,
    }
    # effective independent layer count from error correlation (ask step 2d method)
    # base = single-layer miss rate; joint = both layers miss on PASS-expect rows? use miss on truth
    # Here: "layers both say PASS and are wrong" vs marginal "layer says PASS and is wrong"
    def err_rate(layer):
        wrong = sum(1 for r in R if r["expect"] == "CATCH" and r[layer] == "PASS")
        return wrong / sum(1 for r in R if r["expect"] == "CATCH")
    e10, e13 = err_rate("r10"), err_rate("n13")
    both_wrong = sum(1 for r in R if r["expect"] == "CATCH" and r["r10"] == "PASS" and r["n13"] == "PASS")
    p_both_wrong = both_wrong / sum(1 for r in R if r["expect"] == "CATCH")
    p_indep = e10 * e13
    res["decorrelation"] = {
        "fn_rate_r10_on_truth": e10, "fn_rate_n13_on_truth": e13,
        "both_PASS_on_truth": both_wrong, "P(both_PASS_wrong|truth)": p_both_wrong,
        "P_indep_product": p_indep,
        "observed_over_indep": p_both_wrong / p_indep if p_indep else None,
        # k_eff: (p_both_wrong / p_base) = p_base^(k-1)  -> k = 1 + ln(ratio)/ln(p_base)
        "k_eff_from_joint_PASS_error": 1 + math.log(p_both_wrong / e13) / math.log(e13),
        "k_eff_alt_from_product": 1 + math.log(p_both_wrong / p_indep) / math.log(e13) if p_indep else None,
    }

    # (c) information framework: extra information of 2 layers both CATCH vs 1
    # Let E = "truth is CATCH" (prevalence pi), each layer has sens s, spec c.
    # independent: P(E|C1,C2) = pi*s^2 / (pi*s^2 + (1-pi)*(1-c)^2)
    # one layer:    P(E|C1)   = pi*s   / (pi*s   + (1-pi)*(1-c))
    pi = sum(1 for r in R if r["expect"] == "CATCH") / n
    sens_r10 = sum(1 for r in R if r["expect"] == "CATCH" and r["r10"] == "CATCH") / (pi * n)
    spec_r10 = sum(1 for r in R if r["expect"] == "PASS" and r["r10"] == "PASS") / ((1 - pi) * n)
    sens_n13 = sum(1 for r in R if r["expect"] == "CATCH" and r["n13"] == "CATCH") / (pi * n)
    spec_n13 = sum(1 for r in R if r["expect"] == "PASS" and r["n13"] == "PASS") / ((1 - pi) * n)
    def post1(s, c):
        return pi * s / (pi * s + (1 - pi) * (1 - c))
    def post2_indep(s1, c1, s2, c2):
        return pi * s1 * s2 / (pi * s1 * s2 + (1 - pi) * (1 - c1) * (1 - c2))
    p1_r10, p1_n13 = post1(sens_r10, spec_r10), post1(sens_n13, spec_n13)
    p2_indep = post2_indep(sens_r10, spec_r10, sens_n13, spec_n13)
    # empirical posterior given both CATCH
    p2_emp = sum(1 for r in both_catch if r["expect"] == "CATCH") / len(both_catch)
    # odds & log-odds gain
    def odds(p):
        return p / (1 - p) if p < 1 else float("inf")
    og_emp = odds(p2_emp) / odds(p1_r10)
    res["c_extra_info"] = {
        "prevalence_pi": pi,
        "sens_r10": sens_r10, "spec_r10": spec_r10,
        "sens_n13": sens_n13, "spec_n13": spec_n13,
        "P(E|1_CATCH_r10)": p1_r10, "P(E|1_CATCH_n13)": p1_n13,
        "P(E|2_CATCH_indep_theory)": p2_indep,
        "P(E|2_CATCH_empirical)": p2_emp,
        "odds_gain_1_to_2_indep": odds(p2_indep) / odds(p1_r10),
        "odds_gain_1_to_2_empirical": og_emp,
        "log2_odds_gain_bit_empirical": (float("inf") if og_emp == float("inf")
                                         else math.log2(og_emp)),
        "extra_error_reduction_indep": (1 - p1_r10) - (1 - p2_indep),
        "extra_error_reduction_empirical": (1 - p1_r10) - (1 - p2_emp),
        "note": "empirical is computed on the 20 both-CATCH rows; sample small, "
                "and r10/n13 are NOT independent by code (_ei_02), so the indep "
                "column is a counterfactual upper bound, not an estimate.",
    }
    # generic 90%-agreement scenario (ask 2c): rho=0.9 agreement
    # For balanced binary labels: H(C2|C1) = H(rho) = NEW information carried by
    # the second verdict; I(C1;C2) = 1 - H(rho) = REDUNDANT (shared) information.
    rho = 0.90
    h_rho = h(rho)
    MI_shared = 1.0 - h_rho
    rho_indep = 0.5                       # agreement expected under independence, balanced
    rho_eff = (rho - rho_indep) / (1 - rho_indep)
    n_eff = 2 / (1 + rho_eff)
    res["c_90pct_framework"] = {
        "agreement_rho": rho, "H(second|first)_bit_balanced": h_rho,
        "MI_redundant_bit_balanced": MI_shared,
        "new_info_bit": h_rho, "new_info_pct_of_one_independent_bit": 100.0 * h_rho,
        "redundant_info_bit": MI_shared, "redundancy_pct": 100.0 * MI_shared,
        "independent_rho_expected_balanced": rho_indep,
        "rho_eff_error_correlation": rho_eff,
        "n_eff_design_effect": n_eff,
        "LR_discount_exponent": 1 - rho_eff,
        "formula": "Label level: H(C2|C1)=H(rho)=0.469 bit NEW, I(C1;C2)=1-H(rho)=0.531 bit "
                   "REDUNDANT; a fully independent second layer would add 1.000 bit, so only "
                   "46.9% survives. Truth level: under independence "
                   "P(E|C1,C2)=pi*s1*s2/(pi*s1*s2+(1-pi)*f1*f2) and odds gain = LR1*LR2; "
                   "with correlation, log LR_2|1 = (1-rho_eff)*log LR2, i.e. "
                   "P(E|C1,C2) uses LR1 * LR2^(1-rho_eff). Here rho_eff=(rho-0.5)/0.5=0.8, "
                   "so the second layer contributes only 20% of its nominal log-odds. "
                   "Example: s=0.9, f=0.1 gives LR2=9 (3.170 bit) -> extra 0.634 bit.",
    }

    # (d) residual discriminative power after decorrelation
    # empirical: accuracy of r10 alone / n13 alone / OR-combination / XOR (disagreement only)
    def acc(pred):
        return sum(1 for r in R if pred(r) == r["expect"]) / n
    def fp_fn(pred):
        return (sum(1 for r in R if r["expect"] == "PASS" and pred(r) == "CATCH"),
                sum(1 for r in R if r["expect"] == "CATCH" and pred(r) == "PASS"))
    preds = {
        "r10_only": lambda r: r["r10"],
        "n13_only": lambda r: r["n13"],
        "OR_catch": lambda r: "CATCH" if r["r10"] == "CATCH" or r["n13"] == "CATCH" else "PASS",
        "AND_catch": lambda r: "CATCH" if r["r10"] == "CATCH" and r["n13"] == "CATCH" else "PASS",
        "XOR_needs_human": lambda r: "CATCH" if r["r10"] != r["n13"] else "PASS",
    }
    res["d_residual_power"] = {}
    for k, f in preds.items():
        fp, fn = fp_fn(f)
        res["d_residual_power"][k] = {"acc": acc(f), "correct": int(acc(f) * n),
                                      "fp": fp, "fn": fn}
    # true residual = information in N13 not in R10 = H(N13|R10)
    res["d_residual_power"]["info_residual_bit"] = H_n13_given_r10
    res["d_residual_power"]["info_residual_pct_of_H"] = (
        100.0 * H_n13_given_r10 / H_n13 if H_n13 else None)

    (W / "_ei_03_corr_out.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
