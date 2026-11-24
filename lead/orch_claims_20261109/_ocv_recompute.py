# -*- coding: utf-8 -*-
"""_ocv_recompute.py - independent numeric recomputation from first principles.
Read-only outside stdout. No imports from the _oc_* scripts."""
import math, json

o = {}

# C19: p_all = 2*2^-18 = 2^-17 ; p_fam = 0.25 = 2^-2 ; ratio = 2^15
p_all = 2.0 ** (-17)
p_fam = 2.0 ** (-2)
r19 = p_fam / p_all
o["c19"] = {"p_all": p_all, "p_fam": p_fam, "ratio": r19,
            "log2_ratio": math.log2(r19), "log10_ratio": math.log10(r19),
            "is_32768": r19 == 32768.0, "is_16384": r19 == 16384.0,
            "16384_is_2pow": math.log2(16384.0)}

# C20: 2*2^-n_eff < 0.05 => n_eff > log2(40); n_eff = 18/(1+17*rho)
n_eff_min = math.log2(40.0)
rho = (18.0 / n_eff_min - 1.0) / 17.0
o["c20"] = {"log2_40": n_eff_min, "rho": rho, "round4_rho": round(rho, 4),
            "round4_one_minus_rho": round(1.0 - rho, 4),
            "equals_0p8599": abs(rho - 0.8599) < 1e-9,
            "supplement_equals_0p8599": round(1.0 - rho, 4) == 0.8599,
            "rounded8": round(rho, 8),
            "n_eff_at_rho": 18.0 / (1 + 17 * rho)}

# C3/C4: q_i = fn_i/39 from KEFF_CALC.md:101 (19/39, 35/39, 3/39)
q10, q12, q13 = 19/39, 35/39, 3/39
prod2 = q10 * q13
prod3 = q10 * q12 * q13
fp10, fp12, fp13 = 20/35, 0/35, 0/35
o["c3_c4"] = {"q10": q10, "q12": q12, "q13": q13,
              "two_layer": prod2, "two_layer_pct": 100*prod2,
              "three_layer": prod3, "three_layer_pct": 100*prod3,
              "two_layer_eq_0p037475345": round(prod2, 9) == 0.037475345,
              "three_layer_eq_0p033631720": round(prod3, 9) == 0.033631720,
              "fp_product": fp10*fp12*fp13,
              "fp10": fp10}

# C5: 2.05 = (3/39)/(q10*q13) likelihood ratio; posterior magnification
lik = (3/39) / prod2
post2 = 1 - 0.911215   # placeholder, replaced below from Bayes
# Bayes posterior from KEFF_CALC.md:113-114: claimed correct 91.1215% (2 layer), 91.9589% (3 layer)
e2 = 1 - 0.911215
e3 = 1 - 0.919589
actual_err = 3/18
o["c5"] = {"likelihood_ratio": lik,
           "posterior_err_actual": actual_err,
           "posterior_mag_2layer_using_rounded_pct": actual_err/e2,
           "posterior_mag_3layer_using_rounded_pct": actual_err/e3,
           "posterior_mag_2layer_using_0p088785": actual_err/0.088785,
           "posterior_mag_3layer_using_0p080411": actual_err/0.080411,
           "category_error_4p4474": actual_err/prod2}

# C10: cross table from KEFF_CALC.md:119 (20,20,16,18)
a, b, c, d = 20, 20, 16, 18
n = a+b+c+d
agree = a+d
phi = (b*d - a*c)/math.sqrt((b+c)*(a+d)*(a+b)*(c+d))
# MI from the same 2x2 table (natural-log / log2)
import math as _m
def pl(x):
    return 0.0 if x == 0 else x*math.log2(x/n)
MI = 0.0
for cell in (a,b,c,d):
    MI += pl(cell)
for row in (a+b, c+d):
    MI -= 0.0 if row == 0 else (row/n)*math.log2(row/n)
for col in (a+c, b+d):
    MI -= 0.0 if col == 0 else (col/n)*math.log2(col/n)
# recompute MI properly via joint vs product of marginals
pj = [a/n,b/n,c/n,d/n]; pr=[(a+b)/n,(c+d)/n]; pc=[(a+c)/n,(b+d)/n]
mi = 0.0
for i in range(2):
    for j in range(2):
        p = pj[i*2+j]
        if p>0: mi += p*math.log2(p/(pr[i]*pc[j]))
o["c10"] = {"table": [a,b,c,d], "n": n, "agree": agree, "rate": agree/n,
            "phi": phi, "MI_bit": mi,
            "rate_eq_51p35": round(100*agree/n, 2) == 51.35,
            "phi_eq_0p0293": round(phi, 4) == 0.0293}

# C1/C2: ledger line scan independently (line numbers for the 4 gate names)
import re
ROOT = "D:/Project/ra2-campaign-forge/lead/"
led = {}
for rel in ("PENDING_DECISIONS.md", "GOAL_THREE_TARGETS_20261018.md"):
    lines = open(ROOT+rel, encoding="utf-8").read().splitlines()
    names = ["check_d27.py","check_d28.py","check_d29.py","check_d30.py",
             "_rs_carrier_scan.py","carrier_scan","REFSYNC_SCOPE_FIX","SELF_TEST"]
    led[rel] = {"lines": len(lines),
                "hits": {nm: [i+1 for i,L in enumerate(lines) if nm in L] for nm in names},
                "exit0_exit_lines": [i+1 for i,L in enumerate(lines) if "exit=0" in L]}
ref = open(ROOT+"refsync_scope_20261109/REFSYNC_SCOPE_FIX.md", encoding="utf-8").read().splitlines()
led["REFSYNC_SCOPE_FIX.md"] = {
    "selftest_pass_lines": [i+1 for i,L in enumerate(ref) if "SELF_TEST = PASS" in L],
    "lines_251_253": [ref[250], ref[251], ref[252]],
}
o["c1_c2"] = led

print(json.dumps(o, ensure_ascii=False, indent=2))
