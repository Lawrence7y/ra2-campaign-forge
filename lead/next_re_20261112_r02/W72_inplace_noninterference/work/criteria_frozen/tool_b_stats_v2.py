#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""W68b / CRITERIA_SPEC_V2 — Criterion B with the discrete-field semantic defect fixed.

Derivation: verbatim copy of FROZEN W62 tool_b_stats.py (sha256
4B3AC030668454A60818C774A2A6302F6182441A2CDE594BCC27AA676AB1CD8E) with ONLY the
discrete-field comparable quantity changed from "value -> COUNT multiset" to
"value -> PROPORTION + noise-band/permutation test".

CHANGE MAP (see CRITERIA_SPEC_V2.md):
  * SPEC dict: verbatim, all constants UNCHANGED. Added meta fields only.
  * Continuous path (load/quantile/cv/ks/permutation/jaccard/dframes): verbatim.
  * B-0 / B-3 / B-4 / B-5: verbatim.
  * B-1: additionally checks N_disc(f) > N_max (same N_max, no new constant).
  * B-2: "multiset inequality" -> per-field proportion test conclusion.
  * NEW: proportions / tvd / discrete_noise_band / permutation_pvalue_discrete.

Usage:
  python tool_b_stats_v2.py --selftest --out EVIDENCE\v2_selftest.json
  python tool_b_stats_v2.py --diagnostic ^
      --arm-a W65\out\A_merged.ndjson --arm-b W65\out\B_merged.ndjson ^
      --noise-a1 W65\out\A1.ndjson --noise-a2 W65\out\A2.ndjson ^
      --noise-b1 W65\out\B1.ndjson --noise-b2 W65\out\B2.ndjson ^
      --out RECOMPUTE_DIAGNOSTIC.json
  python tool_b_stats_v2.py --compare <same 6 args> --out result.json

OFFLINE READ-ONLY of source data. I launched 0 / attached 0.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# FROZEN CONSTANTS — CRITERIA_SPEC_V2.md §3 declares EVERY ONE UNCHANGED.
# Verbatim from W62 tool_b_stats.py:35-47.
# ---------------------------------------------------------------------------
SPEC = {
    "n_min": 30,
    "n_noise_min": 2,
    "N_max": 0.30,
    "alpha": 0.05,
    "k_ratio": 2.0,
    "D_floor": 0.05,
    "perm_iters": 2000,
    "seed": 20261113,
    "theta_ui": 0.95,
    "qs": [0.10, 0.25, 0.50, 0.75, 0.90],
    "frozen_at": "2026-11-13T23:25:30+08:00",
}
# Meta fields only — NOT thresholds, NOT new constants.
SPEC_META = {
    "spec_version": "B-W68B-V2-1",
    "criterion_doc": "CRITERIA_SPEC_V2.md",
    "criterion_frozen_at": "2026-11-14T00:33:05.3748807+08:00",
    "discrete_rule": "proportions + TVD + same-arm noise band + permutation test (candidate ii)",
    "frozen_at_note": "SPEC constants above are verbatim FROZEN W62; unchanged in V2",
}
SCHEMA_VERSION = "B-W68B-V2-1"

REQUIRED_FIELDS = ("t", "frame", "map_name", "stage_idx", "end_of_game",
                   "skip_map_select", "battle_idx", "ui_controls")
DISCRETE_FIELDS = ("map_name", "stage_idx", "end_of_game",
                   "skip_map_select", "battle_idx")
VALID_VERDICTS = ("SAME_DISTRIBUTION", "SHIFT_DETECTED", "UNDETERMINABLE")


# ---------------------------------------------------------------------------
# basics — VERBATIM from FROZEN tool_b_stats.py:60-170 (continuous path)
# ---------------------------------------------------------------------------
def load_ndjson(path) -> list[dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            missing = [k for k in REQUIRED_FIELDS if k not in obj]
            if missing:
                raise ValueError(f"{path}:{ln} missing fields {missing}")
            rows.append(obj)
    return rows


def quantile(samples, qs) -> list[float]:
    x = sorted(float(v) for v in samples)
    if not x:
        return [float("nan")] * len(qs)
    out = []
    for q in qs:
        pos = (len(x) - 1) * q
        lo = int(math.floor(pos))
        hi = int(math.ceil(pos))
        if lo == hi:
            out.append(x[lo])
        else:
            out.append(x[lo] + (pos - lo) * (x[hi] - x[lo]))
    return out


def cv(samples) -> float:
    x = [float(v) for v in samples]
    if not x:
        return float("nan")
    m = sum(x) / len(x)
    if m == 0:
        return float("inf")
    var = sum((v - m) ** 2 for v in x) / len(x)
    return math.sqrt(var) / m


def ks_statistic(a, b) -> float:
    a = sorted(float(v) for v in a)
    b = sorted(float(v) for v in b)
    if not a or not b:
        return float("nan")
    grid = sorted(set(a) | set(b))
    i = j = 0
    d = 0.0
    na, nb = len(a), len(b)
    for v in grid:
        while i < na and a[i] <= v:
            i += 1
        while j < nb and b[j] <= v:
            j += 1
        d = max(d, abs(i / na - j / nb))
    return d


def permutation_pvalue(a, b, iters, seed) -> float:
    a = [float(v) for v in a]
    b = [float(v) for v in b]
    d_obs = ks_statistic(a, b)
    pool = a + b
    n_a = len(a)
    rng = random.Random(seed)
    count = 0
    eps = 1e-12
    for _ in range(iters):
        rng.shuffle(pool)
        d_perm = ks_statistic(pool[:n_a], pool[n_a:])
        if d_perm >= d_obs - eps:
            count += 1
    return (count + 1) / (iters + 1)


def jaccard(a, b) -> float:
    sa, sb = set(int(x) for x in a), set(int(x) for x in b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


def jaccard_mean(rows_a, rows_b) -> float:
    # FROZEN semantics retained UNCHANGED (min(n_a,n_b) row truncation).
    # Registered as a residual weakness in CRITERIA_SPEC_V2.md §6 / UNKNOWNS.md.
    n = min(len(rows_a), len(rows_b))
    if n == 0:
        return 0.0
    return sum(jaccard(rows_a[i]["ui_controls"], rows_b[i]["ui_controls"])
               for i in range(n)) / n


def dframes(rows) -> list[int]:
    return [int(rows[i]["frame"]) - int(rows[i - 1]["frame"])
            for i in range(1, len(rows))]


# ---------------------------------------------------------------------------
# V2 discrete path — REPLACES FROZEN multiset()/Counter-equality (§2.3)
# ---------------------------------------------------------------------------
def proportions(rows, field) -> dict:
    """value -> proportion, normalized by THIS ARM's row count (NOT dframe len)."""
    n = len(rows)
    if n == 0:
        return {}
    c = Counter(str(r[field]) for r in rows)
    return {v: cnt / n for v, cnt in c.items()}


def tvd(pa: dict, pb: dict) -> float:
    """Total-variation distance = 0.5*sum|pa-pb| over union of keys. Order-free."""
    u = set(pa) | set(pb)
    return 0.5 * sum(abs(pa.get(v, 0.0) - pb.get(v, 0.0)) for v in u)


def discrete_noise_band(a1, a2, b1, b2, field) -> float:
    """N_disc(f) = max(TVD(A1,A2), TVD(B1,B2)) on proportions; 0.0 if arm noise missing."""
    t = []
    if a1 and a2:
        t.append(tvd(proportions(a1, field), proportions(a2, field)))
    if b1 and b2:
        t.append(tvd(proportions(b1, field), proportions(b2, field)))
    return max(t) if t else 0.0


def permutation_pvalue_discrete(rows_a, rows_b, field, iters, seed) -> tuple[float, str]:
    """p_f for H0 'labels exchangeable'. Pool = all per-row category labels of A++B;
    each permutation repartitions into (n_A, n_B) WITHOUT replacement and recomputes TVD.

    Implemented exactly (not approximately) via multivariate-hypergeometric draws:
    given the pooled category counts, drawing n_A items without replacement for arm A
    is the exact permutation distribution of the count vector. Fixed seed => reproducible.
    Single-category degeneracy returns the analytic exact value p=1.0.
    """
    ca = Counter(str(r[field]) for r in rows_a)
    cb = Counter(str(r[field]) for r in rows_b)
    na, nb = len(rows_a), len(rows_b)
    u = sorted(set(ca) | set(cb))
    pa = {v: ca.get(v, 0) / na for v in u}
    pb = {v: cb.get(v, 0) / nb for v in u}
    t_obs = tvd(pa, pb)
    if len(u) <= 1:
        # every permutation yields identical proportions -> T_perm == T_obs == 0
        return 1.0, "exact_single_category_degeneracy"
    colors = np.array([ca.get(v, 0) + cb.get(v, 0) for v in u], dtype=np.int64)
    rng = np.random.default_rng(seed)
    draws = rng.multivariate_hypergeometric(colors, na, size=iters)  # (iters, |U|)
    p_perm_a = draws / na
    p_perm_b = (colors[None, :] - draws) / nb
    t_perm = 0.5 * np.abs(p_perm_a - p_perm_b).sum(axis=1)
    count = int((t_perm >= t_obs - 1e-12).sum())
    return (count + 1) / (iters + 1), "multivariate_hypergeometric_exact_repartition"


def discrete_field_report(arm_a, arm_b, a1, a2, b1, b2, field) -> dict:
    pa, pb = proportions(arm_a, field), proportions(arm_b, field)
    u = sorted(set(pa) | set(pb))
    n_disc = discrete_noise_band(a1, a2, b1, b2, field)
    t_f = tvd(pa, pb)
    p_f, p_method = permutation_pvalue_discrete(
        arm_a, arm_b, field, SPEC["perm_iters"], SPEC["seed"])
    per_value_delta = {v: pa.get(v, 0.0) - pb.get(v, 0.0) for v in u}
    if n_disc > SPEC["N_max"]:
        verdict = "UNDETERMINABLE_noise_band_unstable"
    elif t_f <= max(n_disc, SPEC["D_floor"]) and p_f >= SPEC["alpha"]:
        verdict = "no_shift_detected"
    else:
        verdict = "shift_detected"
    return {
        "field": field,
        "n_A_rows": len(arm_a), "n_B_rows": len(arm_b),
        "value_set_A": sorted(pa.keys()), "value_set_B": sorted(pb.keys()),
        "value_sets_equal": sorted(pa.keys()) == sorted(pb.keys()),
        "p_A": pa, "p_B": pb,
        "per_value_delta": per_value_delta,
        "occupancy_diff_per_value": {v: abs(d) for v, d in per_value_delta.items()},
        "T_f_tvd": t_f,
        "D_disc": t_f,
        "N_disc": n_disc,
        "p_value": p_f,
        "p_method": p_method,
        "thresholds_used": {"N_max": SPEC["N_max"], "D_floor": SPEC["D_floor"],
                            "alpha": SPEC["alpha"], "perm_iters": SPEC["perm_iters"],
                            "seed": SPEC["seed"]},
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# V2 decision table (CRITERIA_SPEC_V2.md §2.4) — short-circuit order unchanged
# ---------------------------------------------------------------------------
def compare_arms_v2(arm_a, arm_b, a1, a2, b1=None, b2=None) -> dict:
    da, db = dframes(arm_a), dframes(arm_b)
    n_a, n_b = len(da), len(db)
    evidence = {
        "schema_version": SCHEMA_VERSION,
        "spec_meta": SPEC_META,
        "spec": SPEC,
        "n_a": n_a, "n_b": n_b,
        "n_noise_arm_a": 2 if (a1 is not None and a2 is not None) else 0,
        "n_noise_arm_b": 2 if (b1 is not None and b2 is not None) else 0,
    }

    # B-0 : insufficient sample (UNCHANGED)
    if (n_a < SPEC["n_min"] or n_b < SPEC["n_min"]
            or a1 is None or a2 is None
            or evidence["n_noise_arm_a"] < SPEC["n_noise_min"]):
        evidence.update(verdict="UNDETERMINABLE", reason="insufficient_sample",
                        detail=f"n_a={n_a} n_b={n_b} n_min={SPEC['n_min']}")
        return evidence

    d_a1, d_a2 = dframes(a1), dframes(a2)
    N_ks = ks_statistic(d_a1, d_a2)
    D_ks = ks_statistic(da, db)
    p = permutation_pvalue(da, db, SPEC["perm_iters"], SPEC["seed"])
    J = jaccard_mean(arm_a, arm_b)
    Qa, Qb = quantile(da, SPEC["qs"]), quantile(db, SPEC["qs"])
    dQ = max(abs(x - y) for x, y in zip(Qa, Qb))

    disc = {f: discrete_field_report(arm_a, arm_b, a1, a2, b1, b2, f)
            for f in DISCRETE_FIELDS}
    shifted = [f for f, r in disc.items() if r["verdict"] == "shift_detected"]
    unstable = [f for f, r in disc.items()
                if r["verdict"] == "UNDETERMINABLE_noise_band_unstable"]
    max_n_disc = max(r["N_disc"] for r in disc.values())

    evidence.update(
        N_ks=N_ks, D_ks=D_ks, p_value=p,
        J_ui=J, quantile_qs=SPEC["qs"], Q_A=Qa, Q_B=Qb, delta_Q=dQ,
        cv_A=cv(da), cv_B=cv(db),
        max_N_disc=max_n_disc,
        discrete_fields=disc,
        discrete_shifted_fields=shifted,
        discrete_unstable_fields=unstable,
    )

    # B-1 : noise band unstable (continuous OR discrete; same N_max)
    if N_ks > SPEC["N_max"] or unstable:
        evidence.update(verdict="UNDETERMINABLE", reason="noise_band_unstable",
                        detail=f"N_ks={N_ks:.6f} N_max={SPEC['N_max']} "
                               f"discrete_unstable={unstable}")
        return evidence

    # B-2 : discrete proportion shift / UI mismatch
    if shifted or J < SPEC["theta_ui"]:
        evidence.update(verdict="SHIFT_DETECTED", reason="discrete_or_ui_mismatch",
                        detail=f"shifted_fields={shifted} J={J:.6f} theta_ui={SPEC['theta_ui']}")
        return evidence

    # B-3 : same distribution (UNCHANGED)
    if D_ks <= max(N_ks, SPEC["D_floor"]) and p >= SPEC["alpha"]:
        evidence.update(verdict="SAME_DISTRIBUTION", reason="within_noise_band",
                        detail=f"D_ks={D_ks:.6f} <= max(N_ks={N_ks:.6f}, "
                               f"D_floor={SPEC['D_floor']}) and p={p:.6f} >= alpha")
        return evidence

    # B-4 : clear shift (UNCHANGED)
    if D_ks > N_ks * SPEC["k_ratio"] and p < SPEC["alpha"]:
        evidence.update(verdict="SHIFT_DETECTED", reason="ks_beyond_noise",
                        detail=f"D_ks={D_ks:.6f} > N_ks*{SPEC['k_ratio']}="
                               f"{N_ks * SPEC['k_ratio']:.6f} and p={p:.6f} < alpha")
        return evidence

    # B-5 : grey zone (UNCHANGED)
    evidence.update(verdict="UNDETERMINABLE", reason="grey_zone",
                    detail=f"D_ks={D_ks:.6f} N_ks={N_ks:.6f} p={p:.6f}")
    return evidence


# ---------------------------------------------------------------------------
# selftest — V2 must FIX ce_A and KEEP detecting ce_B / ce_C correctly
# ---------------------------------------------------------------------------
def run_selftest(out_dir) -> dict:
    base = Path(__file__).resolve().parent / "EVIDENCE"
    cases = {}
    for tag, expected in (("ce_A", "SAME_DISTRIBUTION"),
                          ("ce_B", "SHIFT_DETECTED"),
                          ("ce_C", "SAME_DISTRIBUTION")):
        d = base / tag
        P = lambda k: load_ndjson(d / f"{k}.ndjson")
        rep = compare_arms_v2(P("A"), P("B"), P("A1"), P("A2"), P("B1"), P("B2"))
        cases[tag] = {"expected": expected, "actual": rep["verdict"],
                      "pass": rep["verdict"] == expected,
                      "reason": rep.get("reason"),
                      "shifted_fields": rep.get("discrete_shifted_fields"),
                      "N_ks": rep.get("N_ks"), "D_ks": rep.get("D_ks"),
                      "p_value": rep.get("p_value")}
    overall = all(c["pass"] for c in cases.values())
    report = {
        "kind": "w68b_v2_selftest",
        "spec_meta": SPEC_META,
        "pre_declared_expectations": {
            "ce_A": "SAME_DISTRIBUTION (defect fixed: row-count difference no longer a shift)",
            "ce_B": "SHIFT_DETECTED (real value difference still detected)",
            "ce_C": "SAME_DISTRIBUTION (control)"},
        "cases": cases, "v2_selftest_pass": overall,
        "note": "synthetic counterexamples only; NOT a real-machine result",
    }
    Path(out_dir).parent.mkdir(parents=True, exist_ok=True)
    Path(out_dir).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


# ---------------------------------------------------------------------------
# diagnostic recompute — READ-ONLY on existing W65 four trips. NOT a formal verdict.
# ---------------------------------------------------------------------------
def run_diagnostic(arm_a, arm_b, a1, a2, b1, b2) -> dict:
    A, B = load_ndjson(arm_a), load_ndjson(arm_b)
    A1, A2, B1, B2 = (load_ndjson(x) for x in (a1, a2, b1, b2))
    rep = compare_arms_v2(A, B, A1, A2, B1, B2)

    diag = {
        "schema_version": "B-W68B-V2-DIAGNOSTIC-1",
        "kind": "DIAGNOSTIC_RECOMPUTE",
        "generated_at": datetime.now(timezone(timedelta(hours=8))).isoformat(),
        "offline_guard": "I launched 0 / attached 0",
        # ---- the three MANDATORY explicit fields ----
        "is_formal_verdict": False,
        "reason_not_formal": (
            "判据变更发生在 W65 四趟采集之后（事后）。按项目 §3.4 与 "
            "REVIEW/LEAD_VERIFY_W65.md §3 的裁定，现有数据一经修正口径即视为污染样本，"
            "不得据此签发正式判定。正式判定须用 CRITERIA_SPEC_V2.md 重新采集的数据"
            "（另一张真机卡负责，不在本卡范围）。本卡不重跑真机、不 attach、不取锁。"),
        "w65_disposition": (
            "维持 SHIFT_DETECTED（附注：触发项为采样时长伪差异）。不篡改 W65 的 "
            "out/b_compare.json，不改写为 SAME_DISTRIBUTION，不重算覆盖历史结果。"),
        "disclaimer": (
            "本文件仅展示新判据在既有四趟数据上的读数，不构成任何等价/不等价结论；"
            "不得写「B 线等价性成立」，不得写「装包无影响」。"),
        "criterion": SPEC_META,
        "spec_constants_unchanged": SPEC,
        "inputs": {
            "arm_a": str(arm_a), "arm_b": str(arm_b),
            "noise_a1": str(a1), "noise_a2": str(a2),
            "noise_b1": str(b1), "noise_b2": str(b2),
            "source": "W65_bline_live_collect/out (READ-ONLY, no re-capture)",
        },
        "row_counts": {"A": len(A), "B": len(B),
                       "A1": len(A1), "A2": len(A2), "B1": len(B1), "B2": len(B2)},
        "continuous_readout": {
            "N_ks": rep["N_ks"], "D_ks": rep["D_ks"], "p_value": rep["p_value"],
            "J_ui": rep["J_ui"], "delta_Q": rep["delta_Q"],
            "Q_A": rep["Q_A"], "Q_B": rep["Q_B"],
            "cv_A": rep["cv_A"], "cv_B": rep["cv_B"],
            "n_a_dframe": rep["n_a"], "n_b_dframe": rep["n_b"],
        },
        "discrete_fields": rep["discrete_fields"],
        "discrete_shifted_fields": rep["discrete_shifted_fields"],
        "discrete_unstable_fields": rep["discrete_unstable_fields"],
        "max_N_disc": rep["max_N_disc"],
        # V2's own decision output, clearly labeled diagnostic-only.
        "diagnostic_verdict": rep["verdict"],
        "diagnostic_reason": rep.get("reason"),
        "diagnostic_detail": rep.get("detail"),
        "formal_verdict": None,
        "weakness_note": (
            "W65 五字段在四趟中均为单一常量值；占比口径下 T_f≡0、p_f≡1，"
            "逐字段判定恒为 no_shift_detected，读数几乎无信息量，不能反推行为等价。"
            "详见 CRITERIA_SPEC_V2.md §6 / UNKNOWNS.md。"),
    }
    return diag


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="W68b CRITERIA_SPEC_V2 stats (offline)")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--diagnostic", action="store_true")
    p.add_argument("--compare", action="store_true")
    p.add_argument("--arm-a"); p.add_argument("--arm-b")
    p.add_argument("--noise-a1"); p.add_argument("--noise-a2")
    p.add_argument("--noise-b1"); p.add_argument("--noise-b2")
    p.add_argument("--out")
    a = p.parse_args(argv)

    if a.selftest:
        if not a.out:
            print("ERROR --selftest needs --out FILE", file=sys.stderr)
            return 2
        rep = run_selftest(a.out)
        for k, c in rep["cases"].items():
            print(f"[{k}] expected={c['expected']} actual={c['actual']} "
                  f"pass={c['pass']} shifted={c['shifted_fields']}")
        print(f"V2_SELFTEST_PASS={rep['v2_selftest_pass']}")
        print("NOTE: synthetic counterexamples only; NOT a real-machine result")
        return 0 if rep["v2_selftest_pass"] else 1

    need = (a.arm_a, a.arm_b, a.noise_a1, a.noise_a2)
    if (a.diagnostic or a.compare) and not all(need):
        print("ERROR needs --arm-a --arm-b --noise-a1 --noise-a2", file=sys.stderr)
        return 2
    if a.diagnostic and not (a.noise_b1 and a.noise_b2):
        print("ERROR --diagnostic needs --noise-b1 --noise-b2", file=sys.stderr)
        return 2

    A, B = load_ndjson(a.arm_a), load_ndjson(a.arm_b)
    A1, A2 = load_ndjson(a.noise_a1), load_ndjson(a.noise_a2)
    B1 = load_ndjson(a.noise_b1) if a.noise_b1 else None
    B2 = load_ndjson(a.noise_b2) if a.noise_b2 else None

    if a.diagnostic:
        out = run_diagnostic(a.arm_a, a.arm_b, a.noise_a1, a.noise_a2,
                             a.noise_b1, a.noise_b2)
    else:
        out = compare_arms_v2(A, B, A1, A2, B1, B2)

    txt = json.dumps(out, indent=2, ensure_ascii=False)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(txt, encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
