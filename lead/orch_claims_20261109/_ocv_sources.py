# -*- coding: utf-8 -*-
"""_ocv_sources.py - dump exact cited line ranges from protected source files.
Read-only. All paths are absolute literals."""
import sys

R = "D:/Project/ra2-campaign-forge/lead/"
SPECS = {
 "s01_PENDING": (R+"PENDING_DECISIONS.md", [(88,95),(103,107),(115,119),(127,131)]),
 "s02_STALE": (R+"stale_pass_20261109/STALE_PASS_INVENTORY.md", [(55,70),(105,109),(140,145),(172,176),(194,205)]),
 "s03_REFSYNC": (R+"refsync_scope_20261109/REFSYNC_SCOPE_FIX.md", [(245,256)]),
 "s04_KEFF": (R+"keff_calc_20261109/KEFF_CALC.md", [(97,120),(254,260)]),
 "s05_KEFF_PY": (R+"keff_calc_20261109/_ke_calc.py", [(33,40),(145,153)]),
 "s06_PVAL": (R+"pvalue_recalc_20261109/PVALUE_RECALC.md", [(110,116),(163,168)]),
 "s07_PVREP": (R+"pvalue_recalc_20261109/_pv_PVALUE_RECALC.md", [(60,68)]),
 "s08_CHAIN": (R+"chain_vs_single_20261109/CHAIN_VS_SINGLE.md", [(90,95),(144,150),(182,187)]),
 "s09_DNEG": (R+"dneg_generative_20261109/DNEG_GENERATIVE.md", [(18,22),(360,370),(461,465)]),
 "s10_REJ32": (R+"gate_rejudge32_20261109/GATE_REJUDGE_32.md", [(49,58),(75,79),(89,96),(135,139),(159,163),(287,291)]),
 "s11_N13": (R+"gate_n13_20261109/GATE_N13_QUOTED_ASSERTION.md", [(388,406),(497,501)]),
 "s12_N4": (R+"n4_gate_verdict_20261109/N4_GATE_VERDICT.md", [(92,96),(199,203),(208,212)]),
 "s13_MINHARD": (R+"minhard_check_20261109/MINHARD_SET_CHECK.md", [(10,14),(171,185)]),
 "s14_MASK": (R+"masking_effect_20261109/MASKING_EFFECT_AUDIT.md", [(61,66),(76,89),(102,112),(371,379)]),
 "s15_FAMILY": (R+"check_family_20261109/CHECK_FAMILY_LINEAGE.md", [(334,338),(408,412),(429,441)]),
 "s16_SD": (R+"score_decomp_20261109/_sd_report.md", [(150,154),(215,221),(261,264),(371,375)]),
 "s17_SCOREDEC": (R+"score_decomp_20261109/SCORE_DECOMP.md", [(16,20)]),
 "s18_H5DES": (R+"h5_governance_20261109/_h5_DESIGN.md", [(281,301)]),
 "s19_H5GOV": (R+"h5_governance_20261109/H5_GOVERNANCE_FIX.md", [(458,480)]),
 "s20_DOCNAME": (R+"gate_doc_name_fix_20261109/GATE_DOC_NAME_FIX.md", [(232,236),(273,277),(300,304)]),
 "s21_EI": (R+"evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md", [(125,132),(140,144),(250,254)]),
 "s22_EIOUT": (R+"evidence_indep_20261109/_ei_03_corr_out.json", [(17,28)]),
 "s23_MINHARD_OUT": (R+"minhard_check_20261109/_mhv_verify_out.txt", [(40,46)]),
 "s24_ME_OUT": (R+"masking_effect_20261109/_me_analyze_out.txt", [(4,9)]),
 "s25_GPV": (R+"gate_pipeline_20261109/_gpv_n13_reg_out.txt", [(130,140)]),
 "s26_DNGLM": (R+"gate_doc_name_fix_20261109/_dn_glm_final.md", [(253,258)]),
}

for key, (path, ranges) in SPECS.items():
    print("=" * 20, key, path.replace(R, "lead/"), "=" * 20)
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except Exception as e:
        print("READ_ERROR:", repr(e))
        continue
    for lo, hi in ranges:
        for n in range(lo, min(hi, len(lines)) + 1):
            print(f"{n}: {lines[n-1]}")
        print("---")
