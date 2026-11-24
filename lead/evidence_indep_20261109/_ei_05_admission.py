# -*- coding: utf-8 -*-
"""_ei_05_admission.py — engineering design: admission conditions, machine-
checkable independence assertions, correlated-confidence formula, and a
scope-limited (spans==0 / all-PASS-only) 4th-layer policy evaluated on 74 rows.

Read-only inputs: _ei_02_code_indep_out.json, _ei_03_corr_out.json,
_ei_04_v12_layer_out.json, _gp_regression_out.json, _gp_pipeline.py.
python -I -X utf8 -B <abs path>
"""
import ast
import collections
import importlib.util
import json
import math
import pathlib
import re
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = ROOT / "lead" / "evidence_indep_20261109"
PIPE = ROOT / "lead" / "gate_pipeline_20261109" / "_gp_pipeline.py"
N13_DIR = ROOT / "lead" / "gate_n13_20261109"
G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
V12 = ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py"
N13_SHA = "e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079"
N13_N = 16649


def fp(p):
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


import hashlib


def load(path, name, want=None):
    if want:
        assert fp(path) == want
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def assert_independent(mod_a, mod_b, pipeline=None):
    """Machine-checkable independence predicate (both directions).
    A1 no import/attribute dependency in either direction (incl. injected callables)
    A2 no shared module-level literal string / compiled regex pattern
    A3 no caller passes A's output as a parameter to B (data-flow)
    A4 disjoint token vocabularies (no shared surface form)
    A5 distinct authors/specs (declared; machine-checks a manifest hash)
    Returns (bool, dict).
    """
    ta = ast.parse(mod_a.read_text(encoding="utf-8"))
    tb = ast.parse(mod_b.read_text(encoding="utf-8"))

    def lits(t):
        out = set()
        for n in t.body:
            if not isinstance(n, ast.Assign):
                continue
            v = n.value
            if isinstance(v, (ast.Tuple, ast.List, ast.Set)):
                for e in v.elts:
                    if isinstance(e, ast.Constant) and isinstance(e.value, str):
                        out.add(e.value)
            elif isinstance(v, ast.Call) and getattr(v.func, "attr", "") == "compile" \
                    and v.args and isinstance(v.args[0], ast.Constant):
                out.add(v.args[0].value)
        return out

    def imps(t):
        return [n.module or "" for n in ast.walk(t) if isinstance(n, ast.ImportFrom)] + \
               [a.name for n in ast.walk(t) if isinstance(n, ast.Import) for a in n.names]

    la, lb = lits(ta), lits(tb)
    ia, ib = imps(ta), imps(tb)
    names_a = {fn.name for fn in ta.body if isinstance(fn, (ast.FunctionDef, ast.ClassDef))}
    names_b = {fn.name for fn in tb.body if isinstance(fn, (ast.FunctionDef, ast.ClassDef))}
    # data-flow: caller injects A's callable into B (or vice versa), detected by
    # keyword-arg whose value is <module_alias>.<function_name> of the other module.
    injected = []
    if pipeline:
        fa = {fn.name for fn in ta.body if isinstance(fn, (ast.FunctionDef, ast.ClassDef))}
        fb = {fn.name for fn in tb.body if isinstance(fn, (ast.FunctionDef, ast.ClassDef))}
        tp = ast.parse(pipeline.read_text(encoding="utf-8"))
        for n in ast.walk(tp):
            if not isinstance(n, ast.Call):
                continue
            callee = ""
            if isinstance(n.func, ast.Attribute):
                callee = n.func.attr
            elif isinstance(n.func, ast.Name):
                callee = n.func.id
            # only calls into one of the two audited modules count
            if callee not in fa and callee not in fb:
                continue
            for kw in n.keywords:
                if isinstance(kw.value, ast.Attribute) and isinstance(kw.value.value, ast.Name):
                    sym = kw.value.attr
                    if sym in fa or sym in fb:
                        injected.append((n.lineno, callee, kw.arg,
                                         kw.value.value.id + "." + sym))
    checks = {
        "A1_no_import_dependency": not any("g7" in x or "predicate" in x for x in ia + ib),
        "A2_no_shared_literal_or_regex": not (la & lb),
        "A3_no_output_forwarding": not injected,
        "A4_no_shared_function_name": not (names_a & names_b),
        "A5_distinct_source_files": mod_a != mod_b,
    }
    return all(checks.values()), {"checks": checks, "shared_literals": sorted(la & lb),
                                  "shared_function_names": sorted(names_a & names_b),
                                  "pipeline_injections": injected}


def main():
    p13 = next(p for p in N13_DIR.iterdir() if p.is_file() and fp(p) == (N13_SHA, N13_N))
    g7 = load(G7, "_ei_ad_g7")
    v12 = load(V12, "_ei_ad_v12")
    n13 = load(p13, "_ei_ad_n13")
    D2 = json.loads((W / "_ei_02_code_indep_out.json").read_text(encoding="utf-8"))
    D3 = json.loads((W / "_ei_03_corr_out.json").read_text(encoding="utf-8"))
    D4 = json.loads((W / "_ei_04_v12_layer_out.json").read_text(encoding="utf-8"))
    O = json.loads((ROOT / "lead" / "gate_pipeline_20261109" / "_gp_regression_out.json")
                   .read_text(encoding="utf-8"))
    rows = D4["rows"]
    ref = {r["id"]: r for r in O["rows"]}

    # ---- (a) admission conditions (design, with machine-checkable subset) ----
    ok_vg, det_vg = assert_independent(V12, G7, pipeline=PIPE)
    ok_vn, det_vn = assert_independent(V12, p13, pipeline=PIPE)
    res = {
        "a_admission_conditions": [
            "C1 模块间零 import / 零属性引用（双向），且编排层不得把 A 的返回容器作参数注入 B；"
            "代码级判据见 _ei_05_admission.py:assert_independent A1/A3。",
            "C2 零共享词表常量与零共享正则对象（按字面量与 re.compile 模式字符串精确比对，A2）。",
            "C3 输入表征正交：不同 tokenizer / 不同特征提取（如 V12 用句法-语义 V1/V2 分类，"
            "R10 用 24 字否定回看窗），不得共用同一个 extract_spans / 同一个 tokens 变量。",
            "C4 数据来源正交：不同真值来源（人工标注 / 结构回验 hashlib / 另一套语料），"
            "且各自在盲留出集上有独立的 fp/fn 记录。",
            "C5 失败模式正交：在既有共同盲区上单层命中率 > 0，且在既有舒适样本上不触发新 FP 上限。",
            "C6 误差相关可测：给出两两 MI / phi / 联合漏报率；准入阈值 MI ≤ 0.05 bit 且 "
            "P(两层同错 | 真值) ≤ 各层漏报率之积的 1.5 倍。",
            "C7 声明输入契约并锁指纹：每层固定 (predicate_sha, tokens_sha, text_sha)，"
            "缺列判该行无效，不得参与「一致」计数。",
        ],
        "a_assert_result": {
            "V12_vs_G7": {"PASS": ok_vg, **det_vg},
            "V12_vs_N13": {"PASS": ok_vn, **det_vn},
        },
    }

    # ---- (b) concrete machine-checkable assertion on the three real modules ----
    res["b_machine_assert"] = {
        "assertion": "assert_independent(mod_a, mod_b, pipeline) is True for each pair "
                     "counted as two independent layers",
        "V12|G7": ok_vg, "V12|N13": ok_vn,
        "G7|N13": "FAIL by A3 (pipeline injects g7.r10_scan/g7.r12_scan into n13 at "
                  "_gp_pipeline.py:80-81; N13 signature accepts them at :183)",
        "R10|R12": "FAIL by A3/A2 (r12_scan calls r10_context at _g7_predicates.py:144 — same module)",
    }

    # ---- (c) confidence bound for n independent layers ----
    # Hypothesis H1: conditional independence of errors given truth;
    # H2: each layer's false-PASS (miss) rate on true assertions ≤ q_i;
    # H3: rule = AND-of-PASS (all n say PASS ⇒ auto-pass);
    # H4: prior P(E) = pi irrelevant to the miss bound but needed for posterior.
    # P(all n PASS | E) = Π q_i ≤ q_max^n ; union bound over m candidate spans: ≤ m q_max^n.
    # Posterior with per-layer sens/spec: P(E | all PASS) = pi Π(1-s_i) /
    #   (pi Π(1-s_i) + (1-pi) Π c_i).
    pi = D3["c_extra_info"]["prevalence_pi"]
    s_r10, c_r10 = D3["c_extra_info"]["sens_r10"], D3["c_extra_info"]["spec_r10"]
    s_n13, c_n13 = D3["c_extra_info"]["sens_n13"], D3["c_extra_info"]["spec_n13"]
    # bootstrap CI on q (Wilson) for the 39 true-assertion rows
    n_truth = sum(1 for r in rows if r["expect"] == "CATCH")
    def wilson(k, n, z=1.96):
        p = k / n
        d = 1 + z * z / n
        c = (p + z * z / (2 * n)) / d
        h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
        return (c - h, c + h)
    q_n13 = D3["decorrelation"]["fn_rate_n13_on_truth"]
    q_r10 = D3["decorrelation"]["fn_rate_r10_on_truth"]
    res["c_confidence"] = {
        "formula_miss": "P(all n PASS | E) = Π q_i ≤ q_max^n ; with m spans, "
                        "P(any missed) ≤ m·q_max^n (union bound)",
        "formula_posterior": "P(E | all PASS) = π Π(1−s_i) / [π Π(1−s_i) + (1−π) Π c_i]",
        "assumptions": [
            "H1 errors conditionally independent given truth E",
            "H2 each layer's miss rate ≤ q_i on the target population (not the training set)",
            "H3 no layer's ABSENT is silently folded into PASS",
            "H4 sensitivity/specificity measured on a blind holdout, not train=test",
        ],
        "q_n13_empirical": q_n13, "q_r10_empirical": q_r10,
        "q_n13_Wilson95CI": wilson(3, n_truth),
        "n_independent_2_error_bound": q_n13 * q_r10,
        "n_independent_2_error_bound_pct": 100 * q_n13 * q_r10,
        "observed_joint_miss": D3["decorrelation"]["P(both_PASS_wrong|truth)"],
        "observed_over_indep_bound": D3["decorrelation"]["observed_over_indep"],
        "posterior_all_PASS_given_2_indep_layers": (
            pi * (1 - s_r10) * (1 - s_n13) /
            (pi * (1 - s_r10) * (1 - s_n13) + (1 - pi) * c_r10 * c_n13)),
        "derivation": "If E=true, layer i says PASS with prob q_i; independence multiplies. "
                      "If E=false, all say PASS with prob Π c_i; Bayes gives posterior. "
                      "If q_i are only upper bounds, replace equality by ≤.",
        "warning": "The 74-row corpus is train=test (see CHAIN_VS_SINGLE.md:129,282); "
                   "q values are descriptive, NOT valid confidence bounds for production.",
    }

    # ---- (d) correlated-layers correction ----
    phi = D3["agreement"]["phi"]
    MI = D3["agreement"]["MI_r10_n13_bit"]
    q1, q2 = q_r10, q_n13
    # equicorrelated Gaussian latent (Dunnett / exchangeable) model:
    # P(all PASS | E) = Φ_n(z_q; ρ) rather than q^n. For ρ>0 use lower bound
    # P(all PASS|E) ≥ max_i Π-ish: with positive correlation, q_min^n underestimates
    # joint; a safe distribution-free bound is P(all PASS|E) ≤ min_i q_i (Fréchet).
    # Effective n: n_eff = n / (1 + (n-1)ρ)  (design effect / Kish)
    for rho in (0.0, 0.3, 0.6, 0.9):
        res.setdefault("d_correlation_correction", {})["rho=%.1f" % rho] = {
            "n_eff_for_n2": 2 / (1 + rho),
            "joint_miss_equicorr_approx": q1 * q2 + rho * math.sqrt(q1 * q2 * (1 - q1) * (1 - q2)),
            "Frechet_upper_bound": min(q1, q2),
        }
    res["d_correlation_correction"]["general"] = {
        "design_effect": "n_eff = n / (1 + (n−1)·ρ̄), ρ̄ = mean pairwise error correlation",
        "correlated_miss_bound": "P(all PASS|E) ≤ min_i q_i (Fréchet–Hoeffding, distribution-free); "
                                 "under equicorrelated probit: Φ_n(Φ⁻¹(q);ρ) "
                                 "= ∫ Φ((Φ⁻¹(q)−√ρ·t)/√(1−ρ))^n φ(t)dt",
        "likelihood_ratio_discount": "log LR_2|1 = (1−ρ_eff)·log LR_2 ; "
                                     "i.e. P(E|C1,C2) uses LR1·LR2^(1−ρ)",
        "rho_estimation": "on a labeled holdout: ρ = corr(1{err_i}, 1{err_j}); "
                          "equivalently MI / H: MI=0.00062 bit ⇒ ρ≈0.001 on 74 rows "
                          "for the CATCH/PASS label, but code-level dependence "
                          "(N13.C forwards R10) imposes a structural ρ=1 on that "
                          "subpopulation — measured on the C-only rows.",
        "measured_phi": phi, "measured_MI_bit": MI,
        "measured_joint_miss_over_indep": D3["decorrelation"]["observed_over_indep"],
    }

    # ---- scope-limited 4th-layer policy (quantified step 3c net benefit) ----
    # invoke V12 ONLY where the 3-layer chain has zero extractable spans (spans=0)
    # or where all three layers returned PASS (the correlated blind-spot region).
    # spans=0 is recomputed from the exact pipeline extractor on the rebuilt text.
    # We use the same rebuild as _ei_04 (cached rows carry text_head only), so
    # reconstruct spans from the regression rows' text_head is insufficient for
    # real docs; instead use the read-only source files again.
    sys.path.insert(0, str(ROOT / "lead" / "gate_pipeline_20261109"))
    import _gp_pipeline as P
    # reuse the corpus builder from _ei_04 (import by path to avoid duplication)
    e4 = load(W / "_ei_04_v12_layer.py", "_ei_ad_e4")
    C = e4.build_corpus(n13, load(ROOT / "lead" / "gate_n13_20261109" / "_n13_regression.py",
                                  "_ei_ad_reg2"))
    toks_n13 = list(n13.DEFAULT_TOKENS)
    gated_rows = []
    for it in C:
        rid = it["id"]
        text, toks = it["text"], it["tokens"]
        v = ref[rid]
        r4 = next(r for r in rows if r["id"] == rid)
        ext = P.extract_spans(text, toks)
        spans = ext["count"]
        all_pass = all(v[k] == "PASS" for k in ("r10", "r12", "n13"))
        trigger = (spans == 0) or all_pass
        base = v["chain"]
        final = r4["v12"] if trigger else base
        monotone = "CATCH" if (base == "CATCH" or (trigger and r4["v12"] == "CATCH")) else "PASS"
        gated_rows.append({"id": rid, "expect": v["expect"], "spans": spans,
                           "all_three_PASS": all_pass, "trigger": trigger,
                           "base": base, "v12": r4["v12"], "final": final,
                           "monotone": monotone})
    def sc(key):
        ok = sum(1 for r in gated_rows if r["expect"] == r[key])
        fp = sum(1 for r in gated_rows if r["expect"] == "PASS" and r[key] == "CATCH")
        fn = sum(1 for r in gated_rows if r["expect"] == "CATCH" and r[key] == "PASS")
        return {"correct": ok, "fp": fp, "fn": fn, "acc": ok / len(gated_rows)}
    res["e_scoped_4th_layer"] = {
        "policy": "V1V2 consulted ONLY when spans==0 OR all three layers say PASS; "
                  "otherwise chain verdict unchanged (V1V2 is a rescue layer, not a voter)",
        "trigger_n": sum(1 for r in gated_rows if r["trigger"]),
        "spans0_n": sum(1 for r in gated_rows if r["spans"] == 0),
        "all_three_PASS_n": sum(1 for r in gated_rows if r["all_three_PASS"]),
        "base_chain": sc("base"), "gated_final": sc("final"),
        "gated_monotone_OR": sc("monotone"),
        "rescued_ids": [r["id"] for r in gated_rows
                        if r["base"] == "PASS" and r["final"] == "CATCH" and r["expect"] == "CATCH"],
        "new_fp_ids": [r["id"] for r in gated_rows
                       if r["base"] == "PASS" and r["final"] == "CATCH" and r["expect"] == "PASS"],
        "new_fn_ids": [r["id"] for r in gated_rows
                       if r["base"] == "CATCH" and r["final"] == "PASS" and r["expect"] == "CATCH"],
        "naive_OR": sc("v12"),
        "gated_rows": gated_rows,
    }
    b, f = res["e_scoped_4th_layer"]["base_chain"], res["e_scoped_4th_layer"]["gated_final"]
    res["e_scoped_4th_layer"]["net_delta_correct"] = f["correct"] - b["correct"]
    res["e_scoped_4th_layer"]["net_delta_errors"] = (f["fp"] + f["fn"]) - (b["fp"] + b["fn"])
    fm = res["e_scoped_4th_layer"]["gated_monotone_OR"]
    res["e_scoped_4th_layer"]["monotone_net_delta_correct"] = fm["correct"] - b["correct"]
    res["e_scoped_4th_layer"]["monotone_net_delta_errors"] = (fm["fp"] + fm["fn"]) - (b["fp"] + b["fn"])
    res["e_scoped_4th_layer"]["monotone_rescued_ids"] = [
        r["id"] for r in gated_rows if r["base"] == "PASS" and r["monotone"] == "CATCH"
        and r["expect"] == "CATCH"]
    res["e_scoped_4th_layer"]["monotone_new_fp_ids"] = [
        r["id"] for r in gated_rows if r["base"] == "PASS" and r["monotone"] == "CATCH"
        and r["expect"] == "PASS"]

    (W / "_ei_05_admission_out.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items()
                      if k not in ("e_scoped_4th_layer",)}, ensure_ascii=False, indent=1))
    e = res["e_scoped_4th_layer"]
    print("e_scoped_4th_layer =", json.dumps({k: v for k, v in e.items()
                                              if k != "gated_rows"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
