# -*- coding: utf-8 -*-
"""_oc_recompute.py : independent recomputation of the numeric claims, read-only."""
import math, json

o = {}

# claim 19: family / all-unit p ratio
p_all = 1 / 131072.0          # 2 * 2^-18, from PVALUE_RECALC.md:103
p_fam = 0.25                  # 1/4, from PVALUE_RECALC.md:105
o["claim19"] = {
    "p_all": p_all, "p_fam": p_fam,
    "ratio": p_fam / p_all,
    "log10": math.log10(p_fam / p_all),
    "as_2pow": math.log2(p_fam / p_all),
    "equals_32768": p_fam / p_all == 32768,
    "equals_16384": p_fam / p_all == 16384,
}

# claim 20: rho bar threshold
needed = math.log2(40.0)
rho = (18.0 / needed - 1) / 17.0
o["claim20"] = {
    "log2_40": needed, "rho_continuous": rho,
    "check_neff_at_rho": 18.0 / (1 + 17 * rho),
    "rho_rounded8": round(rho, 8),
    "equals_0p14013134": round(rho, 8) == 0.14013134,
    "equals_0p8599": abs(rho - 0.8599) < 1e-6,
    "discrete_le_2over17": 2.0 / 17.0,
}

# claim 3/4: q_i = fn_i/39 products
q10, q12, q13 = 19 / 39.0, 35 / 39.0, 3 / 39.0
o["claims_3_4"] = {
    "q_r10": q10, "q_r12": q12, "q_n13": q13,
    "two_layer_q10_q13": q10 * q13,
    "three_layer_q10_q12_q13": q10 * q12 * q13,
    "two_is_3p75pct": round(q10 * q13, 9) == 0.037475345,
    "three_round6": round(q10 * q12 * q13, 6),
    # fp_rate product (the misplaced metric)
    "fp10": 20 / 35.0, "fp12": 0 / 35.0, "fp13": 0 / 35.0,
    "fp_product": (20 / 35.0) * 0.0 * 0.0,
}

# claim 5: 2.05 likelihood vs posterior magnification
post2 = 0.088785            # P(E|2 independent PASS) = posterior ERROR under independence
post3 = 0.080411             # 3 independent layers
actual_err = 3 / 18.0
o["claim5"] = {
    "likelihood_ratio_2p05": (3 / 39.0) / (q10 * q13),
    "posterior_err_actual": actual_err,
    "posterior_mag_2layer": actual_err / post2,
    "posterior_mag_3layer": actual_err / post3,
    "category_error_4p4474": actual_err / (q10 * q13),
}

# claim 10: agreement / phi / MI from 74-row cross table
# CATCH/CATCH=20, CATCH/PASS=20, PASS/CATCH=16, PASS/PASS=18 (KEFF_CALC.md:119)
a, b, c, d = 20, 20, 16, 18
n = a + b + c + d
agree = a + d
phi = (b * d - a * c) / math.sqrt((b + c) * (a + d) * (a + b) * (c + d))
o["claim10"] = {
    "a_b_c_d": [a, b, c, d], "n": n,
    "agree": agree, "rate": agree / n,
    "phi": phi,
}

print(json.dumps(o, ensure_ascii=False, indent=2))
