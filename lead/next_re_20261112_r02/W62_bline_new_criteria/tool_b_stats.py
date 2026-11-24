#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""W62 / Criterion B — observable-behaviour equivalence statistics (offline).

Implements the FROZEN CRITERIA_SPEC.md §2 (frozen 2026-11-13T23:25:30+08:00).
DO NOT change SPEC below after seeing results — project discipline §3.4.

Offline-runnable part of this card:
  * generate synthetic NDJSON traces (two groups: same-distribution POSITIVE
    control, clearly-shifted NEGATIVE control)
  * apply the frozen statistical criterion to both and verify it separates them
Real-machine capture (ReadProcessMemory + EnumWindows) is a LATER card; this
tool only consumes NDJSON produced by that capture layer.

Usage:
  python tool_b_stats.py --gen-synthetic --out EVIDENCE/synth
  python tool_b_stats.py --selftest --out EVIDENCE            # POS + NEG + NEG2
  python tool_b_stats.py --compare --arm-a A.ndjson --arm-b B.ndjson \
      --noise-a1 A1.ndjson --noise-a2 A2.ndjson \
      --noise-b1 B1.ndjson --noise-b2 B2.ndjson --out result.json
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# FROZEN CONSTANTS — CRITERIA_SPEC.md §2.5.  Verbatim.  No post-hoc tuning.
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
SCHEMA_VERSION = "B-W62-1"

REQUIRED_FIELDS = ("t", "frame", "map_name", "stage_idx", "end_of_game",
                   "skip_map_select", "battle_idx", "ui_controls")
DISCRETE_FIELDS = ("map_name", "stage_idx", "end_of_game",
                   "skip_map_select", "battle_idx")
VALID_VERDICTS = ("SAME_DISTRIBUTION", "SHIFT_DETECTED", "UNDETERMINABLE")


# ---------------------------------------------------------------------------
# basics
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


def write_ndjson(path, rows) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


def quantile(samples, qs) -> list[float]:
    """Linear-interpolation (type-7) empirical quantiles."""
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
    """Population coefficient of variation (ddof=0), per SPEC §2.1."""
    x = [float(v) for v in samples]
    if not x:
        return float("nan")
    m = sum(x) / len(x)
    if m == 0:
        return float("inf")
    var = sum((v - m) ** 2 for v in x) / len(x)
    return math.sqrt(var) / m


def ks_statistic(a, b) -> float:
    """Two-sample Kolmogorov-Smirnov statistic = max |F_a(x) - F_b(x)|."""
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
    """(count+1)/(iters+1), fixed seed for reproducibility (SPEC §2.3)."""
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


def multiset(rows, field) -> dict:
    return dict(Counter(str(r[field]) for r in rows))


def jaccard(a, b) -> float:
    sa, sb = set(int(x) for x in a), set(int(x) for x in b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


def jaccard_mean(rows_a, rows_b) -> float:
    n = min(len(rows_a), len(rows_b))
    if n == 0:
        return 0.0
    return sum(jaccard(rows_a[i]["ui_controls"], rows_b[i]["ui_controls"])
               for i in range(n)) / n


def dframes(rows) -> list[int]:
    return [int(rows[i]["frame"]) - int(rows[i - 1]["frame"])
            for i in range(1, len(rows))]


# ---------------------------------------------------------------------------
# the frozen decision table (SPEC §2.4) — short-circuit, no post-hoc tuning
# ---------------------------------------------------------------------------
def compare_arms(arm_a, arm_b, a1, a2, b1=None, b2=None) -> dict:
    da, db = dframes(arm_a), dframes(arm_b)
    n_a, n_b = len(da), len(db)
    evidence = {
        "schema_version": SCHEMA_VERSION,
        "spec_frozen_at": SPEC["frozen_at"],
        "spec": SPEC,
        "n_a": n_a, "n_b": n_b,
        "n_noise_arm_a": 2 if (a1 is not None and a2 is not None) else 0,
        "n_noise_arm_b": 2 if (b1 is not None and b2 is not None) else 0,
    }

    # B-0 : insufficient sample
    if (n_a < SPEC["n_min"] or n_b < SPEC["n_min"]
            or a1 is None or a2 is None
            or evidence["n_noise_arm_a"] < SPEC["n_noise_min"]):
        evidence.update(verdict="UNDETERMINABLE",
                        reason="insufficient_sample",
                        detail=f"n_a={n_a} n_b={n_b} n_min={SPEC['n_min']}")
        return evidence

    d_a1, d_a2 = dframes(a1), dframes(a2)
    N_ks = ks_statistic(d_a1, d_a2)
    D_ks = ks_statistic(da, db)
    p = permutation_pvalue(da, db, SPEC["perm_iters"], SPEC["seed"])
    J = jaccard_mean(arm_a, arm_b)
    Qa, Qb = quantile(da, SPEC["qs"]), quantile(db, SPEC["qs"])
    dQ = max(abs(x - y) for x, y in zip(Qa, Qb))
    discrete_mismatch = {}
    for f in DISCRETE_FIELDS:
        ma, mb = multiset(arm_a, f), multiset(arm_b, f)
        if ma != mb:
            discrete_mismatch[f] = {"A": ma, "B": mb}

    evidence.update(
        N_ks=N_ks, D_ks=D_ks, p_value=p,
        J_ui=J, quantile_qs=SPEC["qs"], Q_A=Qa, Q_B=Qb, delta_Q=dQ,
        cv_A=cv(da), cv_B=cv(db),
        discrete_mismatch=discrete_mismatch,
    )

    # B-1 : noise band itself unstable  (W55b lesson)
    if N_ks > SPEC["N_max"]:
        evidence.update(verdict="UNDETERMINABLE", reason="noise_band_unstable",
                        detail=f"N_ks={N_ks:.6f} > N_max={SPEC['N_max']}")
        return evidence

    # B-2 : discrete fields / UI mismatch
    if discrete_mismatch or J < SPEC["theta_ui"]:
        evidence.update(verdict="SHIFT_DETECTED", reason="discrete_or_ui_mismatch",
                        detail=f"fields={list(discrete_mismatch)} J={J:.6f} "
                               f"theta_ui={SPEC['theta_ui']}")
        return evidence

    # B-3 : same distribution
    if D_ks <= max(N_ks, SPEC["D_floor"]) and p >= SPEC["alpha"]:
        evidence.update(verdict="SAME_DISTRIBUTION", reason="within_noise_band",
                        detail=f"D_ks={D_ks:.6f} <= max(N_ks={N_ks:.6f}, "
                               f"D_floor={SPEC['D_floor']}) and p={p:.6f} >= alpha")
        return evidence

    # B-4 : clear shift
    if D_ks > N_ks * SPEC["k_ratio"] and p < SPEC["alpha"]:
        evidence.update(verdict="SHIFT_DETECTED", reason="ks_beyond_noise",
                        detail=f"D_ks={D_ks:.6f} > N_ks*{SPEC['k_ratio']}="
                               f"{N_ks * SPEC['k_ratio']:.6f} and p={p:.6f} < alpha")
        return evidence

    # B-5 : grey zone
    evidence.update(verdict="UNDETERMINABLE", reason="grey_zone",
                    detail=f"D_ks={D_ks:.6f} N_ks={N_ks:.6f} p={p:.6f}")
    return evidence


# ---------------------------------------------------------------------------
# synthetic traces (offline, deterministic seed) — SPEC §2.6
# ---------------------------------------------------------------------------
def _trace(rng, n, dframe_weights, *, start_frame=1000, battle_idx=1,
           shift=0):
    values = list(dframe_weights.keys())
    weights = list(dframe_weights.values())
    rows = []
    frame = start_frame
    for i in range(n + 1):
        rows.append({
            "t": round(0.006 * i, 6),
            "frame": frame,
            "map_name": "ECH01.MAP" if i < n // 2 else "ECH02.MAP",
            "stage_idx": 0 if i < n // 2 else 1,
            "end_of_game": 0,
            "skip_map_select": 0,
            "battle_idx": battle_idx,
            "ui_controls": [101, 102, 205, 300],
        })
        if i < n:
            frame += rng.choices(values, weights=weights, k=1)[0] + shift
    return rows


# Same distribution for POSITIVE control, and the SPEC-declared shift for the
# NEGATIVE control.  Weights/seed are fixed here so the control is reproducible.
POS_W = {1: 0.25, 2: 0.35, 3: 0.30, 4: 0.10}
NEG_SHIFT = 5            # B arm dframe = same shape, translated by +5
N_SAMPLES = 400          # > SPEC.n_min with margin


def gen_synthetic(out_dir) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SPEC["seed"])
    paths = {}
    # B-POS : all four traces from the SAME distribution, same discrete fields
    for tag in ("A1", "A2", "B1", "B2"):
        p = out / f"pos_{tag}.ndjson"
        write_ndjson(p, _trace(rng, N_SAMPLES, POS_W))
        paths[f"pos_{tag}"] = str(p)
    # B-NEG : A arm unchanged (reuse POS A1/A2), B arm SHIFTED on dframe only
    # (discrete fields stay IDENTICAL on purpose -> exercises B-4, the KS path)
    for tag in ("B1", "B2"):
        p = out / f"neg_{tag}.ndjson"
        write_ndjson(p, _trace(rng, N_SAMPLES, POS_W, shift=NEG_SHIFT))
        paths[f"neg_{tag}"] = str(p)
    # B-NEG2 : discrete-field mismatch (battle_idx) -> exercises B-2
    for tag in ("B1", "B2"):
        p = out / f"neg2_{tag}.ndjson"
        write_ndjson(p, _trace(rng, N_SAMPLES, POS_W, battle_idx=9))
        paths[f"neg2_{tag}"] = str(p)
    paths["_meta"] = {
        "n_samples_per_trace": N_SAMPLES,
        "pos_weights": POS_W, "neg_shift": NEG_SHIFT,
        "seed": SPEC["seed"],
        "note": "synthetic ONLY; not a real-machine capture",
    }
    (out / "synthetic_manifest.json").write_text(
        json.dumps(paths, indent=2, ensure_ascii=False), encoding="utf-8")
    return paths


# ---------------------------------------------------------------------------
# selftest = POS + NEG + NEG2, with PRE-DECLARED expected verdicts (§2.6)
# ---------------------------------------------------------------------------
EXPECTED = {
    "B-POS": "SAME_DISTRIBUTION",
    "B-NEG": "SHIFT_DETECTED",
    "B-NEG2": "SHIFT_DETECTED",
}


def run_selftest(out_dir) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    synth = out / "synth"
    paths = gen_synthetic(synth)

    P = lambda k: load_ndjson(paths[k])
    cases = {}

    cases["B-POS"] = compare_arms(
        _merge(P("pos_A1"), P("pos_A2")), _merge(P("pos_B1"), P("pos_B2")),
        P("pos_A1"), P("pos_A2"), P("pos_B1"), P("pos_B2"))
    cases["B-NEG"] = compare_arms(
        _merge(P("pos_A1"), P("pos_A2")), _merge(P("neg_B1"), P("neg_B2")),
        P("pos_A1"), P("pos_A2"), P("neg_B1"), P("neg_B2"))
    cases["B-NEG2"] = compare_arms(
        _merge(P("pos_A1"), P("pos_A2")), _merge(P("neg2_B1"), P("neg2_B2")),
        P("pos_A1"), P("pos_A2"), P("neg2_B1"), P("neg2_B2"))

    checks = {k: {"expected": EXPECTED[k], "actual": v["verdict"],
                  "pass": v["verdict"] == EXPECTED[k]}
              for k, v in cases.items()}
    overall = all(c["pass"] for c in checks.values())
    report = {
        "schema_version": SCHEMA_VERSION,
        "spec_frozen_at": SPEC["frozen_at"],
        "kind": "w62_b_selftest",
        "pre_declared_expectations": EXPECTED,   # frozen BEFORE running
        "cases": cases,
        "checks": checks,
        "tool_selftest_pass": overall,
        "discipline": "synthetic data only; NOT a real-machine equivalence result",
    }
    (out / "b_selftest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def _merge(*traces):
    """Concatenate independent same-arm traces (SPEC §2.2: A = A1 U A2)."""
    out = []
    for t in traces:
        out.extend(t)
    return out


# ---------------------------------------------------------------------------
def main(argv=None):
    p = argparse.ArgumentParser(description="W62 Criterion B offline stats")
    p.add_argument("--gen-synthetic", action="store_true",
                   help="generate synthetic NDJSON traces")
    p.add_argument("--selftest", action="store_true",
                   help="run POS/NEG/NEG2 controls (declared expectations)")
    p.add_argument("--compare", action="store_true",
                   help="compare real (or supplied) NDJSON arms")
    p.add_argument("--arm-a"); p.add_argument("--arm-b")
    p.add_argument("--noise-a1"); p.add_argument("--noise-a2")
    p.add_argument("--noise-b1"); p.add_argument("--noise-b2")
    p.add_argument("--out", help="output dir (selftest/synth) or json (compare)")
    a = p.parse_args(argv)

    if a.gen_synthetic:
        if not a.out:
            print("ERROR --gen-synthetic needs --out DIR", file=sys.stderr)
            return 2
        paths = gen_synthetic(a.out)
        print(json.dumps({"kind": "synthetic_generated", "paths": paths},
                         indent=2, ensure_ascii=False))
        return 0

    if a.selftest:
        if not a.out:
            print("ERROR --selftest needs --out DIR", file=sys.stderr)
            return 2
        rep = run_selftest(a.out)
        for k, c in rep["checks"].items():
            print(f"[{k}] expected={c['expected']} actual={c['actual']} "
                  f"pass={c['pass']}")
        for k, v in rep["cases"].items():
            print(f"[{k}] N_ks={v.get('N_ks'):.6f} D_ks={v.get('D_ks'):.6f} "
                  f"p={v.get('p_value'):.6f} J={v.get('J_ui'):.4f} "
                  f"reason={v.get('reason')}")
        print(f"TOOL_SELFTEST_PASS={rep['tool_selftest_pass']}")
        print("NOTE: synthetic controls only; NOT a real-machine result")
        return 0 if rep["tool_selftest_pass"] else 1

    if a.compare:
        need = (a.arm_a, a.arm_b, a.noise_a1, a.noise_a2)
        if not all(need):
            print("ERROR --compare needs --arm-a --arm-b --noise-a1 --noise-a2",
                  file=sys.stderr)
            return 2
        b1 = load_ndjson(a.noise_b1) if a.noise_b1 else None
        b2 = load_ndjson(a.noise_b2) if a.noise_b2 else None
        rep = compare_arms(load_ndjson(a.arm_a), load_ndjson(a.arm_b),
                           load_ndjson(a.noise_a1), load_ndjson(a.noise_a2),
                           b1, b2)
        txt = json.dumps(rep, indent=2, ensure_ascii=False)
        if a.out:
            Path(a.out).write_text(txt, encoding="utf-8")
        print(txt)
        return 0

    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
