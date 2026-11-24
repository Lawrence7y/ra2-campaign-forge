# -*- coding: utf-8 -*-
r"""_eind_verify.py — final deliverable session verification (write-domain only).

Runs from source files, not from prior JSON outputs, wherever feasible:
  (1) 9 fingerprints via hashlib
  (2) precise AST module-level literal comparison (str/Tuple/List/Set/re.compile)
      -- fixes the _ei_05_admission.py:59-72 detector which misses bare str
  (3) N13 forwards R10 / R12 reuse / V12 re-use: exact line evidence
  (4) 74-row cross table, agreement, phi, MI, posterior ladder, k_eff
  (5) 4th layer V1V2 on the 74-row corpus (rebuilt from read-only sources)
      + net-benefit variants + 20-row holdout scores
  (6) readonly integrity snapshot (before/after handled by caller)

python -I -X utf8 -B D:/Project/ra2-campaign-forge/lead/evidence_indep_20261109/_eind_verify.py
"""
import ast
import hashlib
import importlib.util
import json
import math
import pathlib
import re
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = ROOT / "lead" / "evidence_indep_20261109"
N13_DIR = ROOT / "lead" / "gate_n13_20261109"
N13_SHA = "e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079"
N13_N = 16649

FP = {
    "lead/gate_n13_20261109/_n13_predicates.py": ("e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649),
    "lead/gate_v1v2_20261109/_v12_rule.py": ("15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0", 9148),
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/gate_pipeline_20261109/_gp_pipeline.py": ("25c7753f097b8e98e1abb424419e42780bc1ed94fed4a674c142be6c6c1625a7", 15811),
    "lead/gate_pipeline_20261109/_gp_regression_out.json": ("d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
    "lead/chain_vs_single_20261109/_cs_align_out.json": ("9dc062202fd9c00b2b74ce6393f29a90f18012a9914cf18dc9cd7ffa653f2698", 11594),
    "lead/chain_vs_single_20261109/_cs_BASELINE_ALIGNMENT_20261109.md": ("3397c1c41b0a81e85699f07ce608b9b13e0ab45cba51280a3e78883581768ed2", 49850),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}


def fp(p):
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def load(p, name):
    spec = importlib.util.spec_from_file_location(name, str(p))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def precise_literals(p):
    """Return {literal_value: [(lineno, target_name)]} for ALL module-level
    Assign/AnnAssign whose value is Constant(str), Tuple/List/Set of str
    Constants, or a re.compile(...) call with a literal first argument.
    This is the corrected A2 detector (writer's version missed bare str)."""
    tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    out = {}

    def rec(items, lineno, name):
        for e in items:
            if isinstance(e, ast.Constant) and isinstance(e.value, str):
                out.setdefault(e.value, []).append((lineno, name))

    def names(t):
        return [t.id] if isinstance(t, ast.Name) else []

    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = [n for t in node.targets for n in names(t)]
            nm = targets[0] if targets else "<anon>"
            v = node.value
            lineno = node.lineno
        elif isinstance(node, ast.AnnAssign):
            nm = names(node.target)[0] if names(node.target) else "<anon>"
            v, lineno = node.value, node.lineno
        else:
            continue
        if v is None:
            continue
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            out.setdefault(v.value, []).append((lineno, nm))
        elif isinstance(v, (ast.Tuple, ast.List, ast.Set)):
            rec(v.elts, lineno, nm)
        elif isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) \
                and v.func.attr == "compile" and v.args \
                and isinstance(v.args[0], ast.Constant) and isinstance(v.args[0].value, str):
            out.setdefault(v.args[0].value, []).append((lineno, nm))
    return out


def main():
    out = {}
    # ---- (1) fingerprints ----
    fpr = {}
    n13_real_name = None
    for k, (sha, n) in FP.items():
        cand = ROOT / k
        if cand.is_file() and fp(cand) == (sha, n):
            fpr[k] = {"expect": [sha, n], "got": list(fp(cand)), "match": True}
            if (sha, n) == (N13_SHA, N13_N):
                n13_real_name = cand.name
        else:
            hits = [p for p in sorted(N13_DIR.iterdir()) if p.is_file() and fp(p) == (sha, n)]
            fpr[k] = {"resolved": hits[0].name if len(hits) == 1 else None,
                      "hits": len(hits), "match": len(hits) == 1}
            if len(hits) == 1 and (sha, n) == (N13_SHA, N13_N):
                n13_real_name = hits[0].name
    out["fingerprints"] = fpr
    out["fingerprints_all_match"] = all(v["match"] for v in fpr.values())
    out["n13_real_name"] = n13_real_name
    assert n13_real_name is not None, "N13 fingerprint not uniquely found"
    n13path = N13_DIR / n13_real_name

    paths = {"N13": n13path,
             "G7": ROOT / "lead/gate_fp7_20261108/_g7_predicates.py",
             "V12": ROOT / "lead/gate_v1v2_20261109/_v12_rule.py",
             "PIPE": ROOT / "lead/gate_pipeline_20261109/_gp_pipeline.py"}

    # ---- (2) precise A2 ----
    lits = {k: precise_literals(p) for k, p in paths.items() if k != "PIPE"}
    a2 = {}
    for a, b in (("V12", "G7"), ("V12", "N13"), ("G7", "N13")):
        both = sorted(set(lits[a]) & set(lits[b]))
        a2[a + "|" + b] = {
            "precise_shared_module_level_literals": [
                {"value": repr(v), "in_a": lits[a][v], "in_b": lits[b][v]} for v in both],
            "count": len(both), "precise_A2_pass": len(both) == 0}
    out["A2_precise"] = a2
    # import / forwarding / reuse line evidence
    src = {k: p.read_text(encoding="utf-8").splitlines() for k, p in paths.items()}
    def hits(lines, pat):
        return [i + 1 for i, s in enumerate(lines) if re.search(pat, s)]
    out["line_evidence"] = {
        "N13_r13_scan_signature": hits(src["N13"], r"^def r13_scan\("),
        "N13_calls_r10_scan": hits(src["N13"], r"rhits = r10_scan\("),
        "N13_calls_r12_scan": hits(src["N13"], r"dhits = r12_scan\("),
        "N13_records_r10_kind": hits(src["N13"], r'"r10_kind": r10_map\.get'),
        "N13_C_gated_on_r10_kind": hits(src["N13"], r'k in \("negation", "quote_mention"\)'),
        "N13_C_emits_kind": hits(src["N13"], r'rec\.update\(kind="C"'),
        "N13_consumes_R12": hits(src["N13"], r"in r12_pos"),
        "PIPE_injects_g7_into_n13": hits(src["PIPE"], r"r10_scan=g7\."),
        "G7_r12_calls_r10_context": hits(src["G7"], r"ctx = r10_context\("),
        "G7_CLAUSE_BREAK_def": hits(src["G7"], r"^CLAUSE_BREAK ="),
        "G7_CLAUSE_BREAK_used": hits(src["G7"], r"for ch in CLAUSE_BREAK"),
        "V12_CLAUSE_SEPS_def": hits(src["V12"], r"^_CLAUSE_SEPS ="),
        "V12_CLAUSE_SEPS_used": hits(src["V12"], r"_segment\(line, rel, _CLAUSE_SEPS\)"),
        "V12_only_import": hits(src["V12"], r"^import re$"),
        "V12_V2_OVERRIDE_def": hits(src["V12"], r"^V2_OVERRIDE = \("),
        "V12_shared_已入账": hits(src["V12"], r'"已入账"'),
        "N13_DEFAULT_TOKENS_def": hits(src["N13"], r"^DEFAULT_TOKENS = \("),
    }

    # ---- (3) 74-row stats from read-only regression JSON ----
    O = json.loads((ROOT / "lead/gate_pipeline_20261109/_gp_regression_out.json").read_text(encoding="utf-8"))
    rows = O["rows"]
    assert len(rows) == 74
    cross = {}
    for r in rows:
        cross[r["r10"] + "|" + r["n13"]] = cross.get(r["r10"] + "|" + r["n13"], 0) + 1
    # n11=X=CATCH&Y=CATCH (=b), n10=CATCH|PASS (=c),
    # n01=PASS|CATCH (=a), n00=PASS|PASS (=d).
    a, b, c, d = cross["PASS|CATCH"], cross["CATCH|CATCH"], cross["CATCH|PASS"], cross["PASS|PASS"]
    n = len(rows)
    agree = b + d
    phi = (b * d - a * c) / math.sqrt((b + c) * (a + d) * (a + b) * (c + d))
    def H(p):
        return 0.0 if p <= 0 or p >= 1 else -p * math.log2(p) - (1 - p) * math.log2(1 - p)
    pA = (a + b) / n
    pB = (a + c) / n
    mi = 0.0
    for i, j in (("PASS", "PASS"), ("PASS", "CATCH"), ("CATCH", "PASS"), ("CATCH", "CATCH")):
        pxy = cross[i + "|" + j] / n
        px = (cross[i + "|PASS"] + cross[i + "|CATCH"]) / n
        py = (cross["PASS|" + j] + cross["CATCH|" + j]) / n
        if pxy > 0:
            mi += pxy * math.log2(pxy / (px * py))
    Hn = H(pB)
    Hng = sum((cross[i + "|" + j] / n) * H(cross[i + "|" + j] / (cross[i + "|PASS"] + cross[i + "|CATCH"]))
              for i in ("PASS", "CATCH") for j in ("PASS", "CATCH")
              if cross[i + "|PASS"] + cross[i + "|CATCH"])
    out["stats74"] = {"n": n, "cross": cross, "agree": agree, "agree_pct": 100 * agree / n,
                      "phi": phi, "MI_bit": mi, "H_n13_bit": Hn, "H_n13_given_r10_bit": Hng,
                      "residual_info_pct": 100 * Hng / Hn}

    # posterior ladder (all PASS subsets)
    ladder = {}
    for label, keys in (("prior", ()), ("n13", ("n13",)),
                        ("n13+r10", ("n13", "r10")),
                        ("n13+r10+r12", ("n13", "r10", "r12"))):
        sub = [r for r in rows if all(r[k] == "PASS" for k in keys)]
        wrong = sum(1 for r in sub if r["expect"] == "CATCH")
        ladder[label] = {"n_pass": len(sub), "wrong": wrong,
                         "P_CATCH_given_allPASS": wrong / len(sub)}
    pi = sum(1 for r in rows if r["expect"] == "CATCH") / n
    q13 = sum(1 for r in rows if r["expect"] == "CATCH" and r["n13"] == "PASS") / sum(1 for r in rows if r["expect"] == "CATCH")
    q10 = sum(1 for r in rows if r["expect"] == "CATCH" and r["r10"] == "PASS") / sum(1 for r in rows if r["expect"] == "CATCH")
    p1 = ladder["n13"]["P_CATCH_given_allPASS"]
    p3 = ladder["n13+r10+r12"]["P_CATCH_given_allPASS"]
    k_odds = math.log((p3 / (1 - p3)) / (pi / (1 - pi))) / math.log((p1 / (1 - p1)) / (pi / (1 - pi)))
    k_prob_ratio = math.log(p3 / pi) / math.log(p1 / pi)
    I1 = pi - p1          # upstream _cs_info.py:26 uses base[2] - p
    I3 = pi - p3
    out["posterior"] = {"pi": pi, "q_n13": q13, "q_r10": q10, "q_product": q13 * q10,
                        "ladder": ladder, "R12_increment_bit": math.log2(
                            (ladder["n13+r10+r12"]["P_CATCH_given_allPASS"] / (1 - ladder["n13+r10+r12"]["P_CATCH_given_allPASS"]))
                            / (ladder["n13+r10"]["P_CATCH_given_allPASS"] / (1 - ladder["n13+r10"]["P_CATCH_given_allPASS"]))),
                        "k_eff_posterior_odds": k_odds,
                        "k_eff_probability_ratio_upstream": k_prob_ratio,
                        "I1_linear": I1, "I3_linear": I3,
                        "info_gain_ratio_linear": I3 / I1,
                        "allPASS_error_observed": p3,
                        "observed_over_indep": q13 / (q13 * q10)}
    # ---- (4b) confidence formula numbers (computed here, not merely quoted) ----
    nE = sum(1 for r in rows if r["expect"] == "CATCH")
    nN = n - nE
    c13 = sum(1 for r in rows if r["expect"] == "PASS" and r["n13"] == "PASS") / nN
    c10 = sum(1 for r in rows if r["expect"] == "PASS" and r["r10"] == "PASS") / nN
    num = pi * q13 * q10
    den = num + (1 - pi) * c13 * c10
    z, k = 1.96, 3
    nq = nE
    ph = k / nq
    wil_lo = (ph + z * z / (2 * nq) - z * math.sqrt(ph * (1 - ph) / nq + z * z / (4 * nq * nq))) / (1 + z * z / nq)
    wil_hi = (ph + z * z / (2 * nq) + z * math.sqrt(ph * (1 - ph) / nq + z * z / (4 * nq * nq))) / (1 + z * z / nq)
    out["confidence"] = {"pi": pi, "nE": nE, "nN": nN,
                         "q_n13": q13, "q_r10": q10, "c_n13": c13, "c_r10": c10,
                         "joint_miss_indep_expectation": q13 * q10,
                         "Frechet_upper_bound_min_q": min(q13, q10),
                         "P_E_given_2_indep_allPASS": num / den,
                         "q_n13_Wilson95": [wil_lo, wil_hi],
                         "note": "q13*q10 is the INDEPENDENCE EXPECTATION, not a distribution-free upper bound; "
                                 "the distribution-free upper bound is min(q_i). 74 rows are train=test."}
    # ---- (4) token contract ----
    fam = {}
    for r in rows:
        fam.setdefault(tuple(r["tokens"]), 0)
        fam[tuple(r["tokens"])] += 1
    T3 = ("已入账", "已追加", "已生效")
    out["token_contract"] = {"families": {str(list(k)): v for k, v in fam.items()},
                             "identical_to_DEFAULT_TOKENS_rows": fam.get(T3, 0),
                             "superset_of_T3_rows": sum(v for k, v in fam.items() if set(T3) <= set(k))}

    # ---- (5) V1V2 4th layer on exact 74-row corpus ----
    n13 = load(n13path, "_eind_n13")
    v12 = load(paths["V12"], "_eind_v12")
    e4 = load(W / "_ei_04_v12_layer.py", "_eind_e4")
    reg = load(ROOT / "lead/gate_n13_20261109/_n13_regression.py", "_eind_reg")
    C = e4.build_corpus(n13, reg)
    assert [x["id"] for x in C] == [r["id"] for r in rows], "corpus id mismatch"
    sys.path.insert(0, str(ROOT / "lead/gate_pipeline_20261109"))
    import _gp_pipeline as P
    T = list(n13.DEFAULT_TOKENS)

    def v12_detail(text):
        hs = []
        for tok in sorted(set(list(v12.V2_OVERRIDE) + T), key=len, reverse=True):
            for m in re.finditer(re.escape(tok), text):
                c = v12.classify_v12(text, m.start(), m.end(), tok)
                if c["verdict"] == "V2":
                    hs.append({"token": tok, "override": c["override"],
                               "review": c["review_flag"], "hard": c["hard"]})
        return {"catch": bool(hs), "hard_override": any(h["override"] for h in hs),
                "only_default": bool(hs) and all(h["review"] for h in hs), "hits": hs}

    work = []
    for it, vr in zip(C, rows):
        d = v12_detail(it["text"])
        work.append({"id": it["id"], "expect": vr["expect"], "base": vr["chain"],
                     "spans": P.extract_spans(it["text"], it["tokens"])["count"],
                     "all_pass": all(vr[k] == "PASS" for k in ("r10", "r12", "n13")),
                     "v12": "CATCH" if d["catch"] else "PASS",
                     "hard_override": d["hard_override"], "only_default": d["only_default"],
                     "v12_hits": d["hits"]})

    def sc(finals):
        ok = sum(1 for r, f in zip(work, finals) if r["expect"] == f)
        fpos = sum(1 for r, f in zip(work, finals) if r["expect"] == "PASS" and f == "CATCH")
        fneg = sum(1 for r, f in zip(work, finals) if r["expect"] == "CATCH" and f == "PASS")
        return {"correct": ok, "fp": fpos, "fn": fneg, "acc": ok / len(work),
                "delta_correct": ok - 69}

    V = {}
    V["0_baseline_chain"] = [r["base"] for r in work]
    V["1_naive_OR_all4"] = ["CATCH" if r["base"] == "CATCH" or r["v12"] == "CATCH" else "PASS" for r in work]
    V["2_monotone_spans0_or_allPASS"] = ["CATCH" if r["base"] == "CATCH" or
        ((r["spans"] == 0 or r["all_pass"]) and r["v12"] == "CATCH") else "PASS" for r in work]
    V["3_monotone_spans0_only"] = ["CATCH" if r["base"] == "CATCH" or
        (r["spans"] == 0 and r["v12"] == "CATCH") else "PASS" for r in work]
    V["4_monotone_spans0_hard_override"] = ["CATCH" if r["base"] == "CATCH" or
        (r["spans"] == 0 and r["v12"] == "CATCH" and r["hard_override"]) else "PASS" for r in work]
    V["5_monotone_allPASS_hard_override"] = ["CATCH" if r["base"] == "CATCH" or
        (r["all_pass"] and r["v12"] == "CATCH" and r["hard_override"]) else "PASS" for r in work]
    V["6_monotone_gated_hard_override"] = ["CATCH" if r["base"] == "CATCH" or
        ((r["spans"] == 0 or r["all_pass"]) and r["v12"] == "CATCH" and r["hard_override"]) else "PASS" for r in work]
    net = {}
    for k, finals in V.items():
        s = sc(finals)
        s["rescued_fn"] = [r["id"] for r, f in zip(work, finals)
                           if r["base"] == "PASS" and f == "CATCH" and r["expect"] == "CATCH"]
        s["new_fp"] = [r["id"] for r, f in zip(work, finals)
                       if r["base"] == "PASS" and f == "CATCH" and r["expect"] == "PASS"]
        net[k] = s
    gpA = [{"id": r["id"], **{k: r[k] for k in
            ("spans", "all_pass", "v12", "hard_override", "only_default", "v12_hits")}}
           for r in work if r["id"].startswith("GP-A")]
    HOLD = json.loads((ROOT / "lead/chain_vs_single_20261109/_cs_holdout_out.json").read_text(encoding="utf-8"))["unseen"]
    hold = {"n": len(HOLD), "correct": sum(1 for r in HOLD if r["expect"] == r["v12"]),
            "fp": sum(1 for r in HOLD if r["expect"] == "PASS" and r["v12"] == "CATCH"),
            "fn": sum(1 for r in HOLD if r["expect"] == "CATCH" and r["v12"] == "PASS")}
    # 3 holdout rows are verbatim duplicates of GP-A2/A3/A1 (read-only check)
    corpus_texts = {x["text"] for x in C}
    hold["verbatim_duplicate_ids"] = [r["id"] for r in HOLD if r["text"] in corpus_texts]
    out["fourth_layer"] = {"v12_single_layer": sc([r["v12"] for r in work]),
                           "GP_A_detail": gpA, "variants": net, "holdout": hold,
                           "spans0_n": sum(1 for r in work if r["spans"] == 0),
                           "all_pass_n": sum(1 for r in work if r["all_pass"])}

    # ---- (6) extra-info framework at rho=0.9 (label level) ----
    rho = 0.9
    h2 = H(rho)
    out["extra_info_90pct"] = {"H_second_given_first_bit": h2, "MI_redundant_bit": 1 - h2,
                               "new_info_pct_of_1bit": 100 * h2,
                               "rho_eff": (rho - 0.5) / 0.5,
                               "n_eff_design": 2 / (1 + (rho - 0.5) / 0.5),
                               "LR2_bit_nominal": math.log2(9),
                               "LR2_bit_discounted": (1 - (rho - 0.5) / 0.5) * math.log2(9)}

    # ---- (7) train=test error-indicator correlation (DESCRIPTIVE ONLY) ----
    # rho = corr(1{err_i}, 1{err_j}) over the 74 rows; this is NOT the required
    # blind-holdout double check, because the 74 rows are train=test.
    def err(r, k):
        return 1 if r[k] != r["expect"] else 0
    e10 = [err(r, "r10") for r in rows]
    e13 = [err(r, "n13") for r in rows]
    e12 = [err(r, "r12") for r in rows]

    def phi_corr(x, y):
        mx, my = sum(x) / len(x), sum(y) / len(y)
        num = sum((a - mx) * (b - my) for a, b in zip(x, y))
        dx = math.sqrt(sum((a - mx) ** 2 for a in x))
        dy = math.sqrt(sum((b - my) ** 2 for b in y))
        return num / (dx * dy) if dx and dy else float("nan")
    out["train_test_error_corr_DESCRIPTIVE_ONLY"] = {
        "rho_r10_n13": phi_corr(e10, e13),
        "rho_r10_r12": phi_corr(e10, e12),
        "joint_err_r10_n13": sum(1 for a, b in zip(e10, e13) if a and b),
        "joint_err_r10_r12": sum(1 for a, b in zip(e10, e12) if a and b),
        "warning": "74 rows are train=test (CHAIN_VS_SINGLE.md:129,282); these are descriptive, NOT a blind-holdout double check."}

    hold_cols = sorted({k for r in HOLD for k in r})
    out["holdout_columns"] = hold_cols
    out["holdout_error_corr_feasible"] = "r10" in hold_cols and "r12" in hold_cols
    out["holdout_error_corr_note"] = (
        "rho=corr(1{err_i},1{err_j}) cannot be computed on this holdout: "
        "no r10/r12 per-row columns; 3/20 rows are verbatim GP-A duplicates. "
        "A blind holdout with all four layer columns is REQUIRED but not present.")

    (W / "_eind_verify_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"fingerprints_all_match": out["fingerprints_all_match"],
                      "A2_precise": {k: {"shared": [x["value"] for x in v["precise_shared_module_level_literals"]],
                                        "pass": v["precise_A2_pass"]} for k, v in a2.items()},
                      "stats74": out["stats74"],
                      "posterior": out["posterior"],
                      "fourth_layer": {"v12_single_layer": out["fourth_layer"]["v12_single_layer"],
                                       "variants": {k: {"correct": v["correct"], "fp": v["fp"], "fn": v["fn"],
                                                       "delta_correct": v["delta_correct"]}
                                                    for k, v in net.items()},
                                       "holdout": hold},
                      "line_evidence": out["line_evidence"],
                      }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
