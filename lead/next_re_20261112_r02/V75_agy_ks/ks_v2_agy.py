#!/usr/bin/env python3
"""Independent two-sample KS and permutation verifier for NDJSON frame deltas."""

import json
import random
import sys
from collections import Counter

CLAIMED_D_KS = 0.0000488782
N_PERM = 2000
SEED = 20261113
QUANTILES = (0.1, 0.25, 0.5, 0.75, 0.9)


def load_dframes(path):
    """Read 'frame' per NDJSON line and compute dframe[i] = frame[i] - frame[i-1]."""
    frames = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            s = line.strip()
            if s:
                frames.append(int(json.loads(s)["frame"]))
    if len(frames) < 2:
        raise ValueError(f"{path}: need >= 2 records to difference, got {len(frames)}")
    dframes = [frames[i] - frames[i - 1] for i in range(1, len(frames))]
    neg_count = sum(1 for d in dframes if d < 0)
    return dframes, neg_count


def ks_precompute(x, y):
    """Compute exact two-sample KS numerator and precomputed permutation tables.

    Tie/lattice convention:
      Uses right-continuous ECDFs F_A(v) = #{a <= v}/n_A and F_B(v) = #{b <= v}/n_B
      evaluated at each unique value v in the pooled sorted support (ties grouped
      together, so sup_{x in R} |F_A(x) - F_B(x)| equals max over unique support).
      Uses exact integer numerator |N * A_k - n_A * C_k| = (n_A * n_B) * |F_A - F_B|.
    """
    n_x, n_y = len(x), len(y)
    if n_x == 0 or n_y == 0:
        raise ValueError("Both samples must be non-empty.")
    n_tot = n_x + n_y
    cx, cy = Counter(x), Counter(y)
    support = sorted(cx.keys() | cy.keys())
    rank_of = {v: i for i, v in enumerate(support)}
    cum_pool = []
    tot = a_cum = obs_num = 0
    for v in support:
        tot += cx[v] + cy[v]
        a_cum += cx[v]
        cum_pool.append(tot)
        diff = abs(n_tot * a_cum - n_x * tot)
        if diff > obs_num:
            obs_num = diff
    return n_x, n_y, cum_pool, rank_of, obs_num


def ks_stat(x, y):
    n_x, n_y, _, _, obs_num = ks_precompute(x, y)
    return obs_num / (n_x * n_y)


def permutation_p(x, y, n_perm=N_PERM, seed=SEED):
    n_x, n_y, cum_pool, rank_of, obs_num = ks_precompute(x, y)
    n_tot = n_x + n_y
    k_buckets = len(cum_pool)
    # Precompute pooled bucket indices once; never re-sort inside the permutation loop.
    buckets = [rank_of[v] for v in x] + [rank_of[v] for v in y]
    rng = random.Random(seed)
    ge_count = 0
    for _ in range(n_perm):
        rng.shuffle(buckets)
        counts_a = [0] * k_buckets
        for b in buckets[:n_x]:
            counts_a[b] += 1
        a_cum = perm_num = 0
        for idx in range(k_buckets):
            a_cum += counts_a[idx]
            diff = abs(n_tot * a_cum - n_x * cum_pool[idx])
            if diff > perm_num:
                perm_num = diff
        if perm_num >= obs_num:
            ge_count += 1
    p_val = (ge_count + 1) / (n_perm + 1)
    return obs_num / (n_x * n_y), p_val, ge_count


def quantiles(vals, probs=QUANTILES):
    s = sorted(vals)
    n = len(s)
    out = {}
    for q in probs:
        pos = q * (n - 1)
        lo = int(pos)
        hi = min(lo + 1, n - 1)
        frac = pos - lo
        out[q] = s[lo] * (1.0 - frac) + s[hi] * frac
    return out


def main():
    if len(sys.argv) != 3:
        sys.exit(f"Usage: {sys.argv[0]} <arm_A.ndjson> <arm_B.ndjson>")
    d_a, neg_a = load_dframes(sys.argv[1])
    d_b, neg_b = load_dframes(sys.argv[2])
    n_a, n_b = len(d_a), len(d_b)
    d_obs, p_val, ge_count = permutation_p(d_a, d_b)
    n_ks_a = ks_stat(d_a[: n_a // 2], d_a[n_a // 2 :])
    n_ks_b = ks_stat(d_b[: n_b // 2], d_b[n_b // 2 :])
    q_a, q_b = quantiles(d_a), quantiles(d_b)
    diff_d = abs(d_obs - CLAIMED_D_KS)
    verdict = "AGREE" if (diff_d <= 1e-6 and p_val >= 0.95) else "DISAGREE"

    print(f"n_A: {n_a} (negative_deltas={neg_a})")
    print(f"n_B: {n_b} (negative_deltas={neg_b})")
    print(f"D_ks: {d_obs:.10f}")
    print(f"p_value: {p_val:.6f} (ge_count={ge_count}/{N_PERM}, seed={SEED})")
    print(f"N_ks_A: {n_ks_a:.10f}")
    print(f"N_ks_B: {n_ks_b:.10f}")
    print("Quantiles_A: " + ", ".join(f"{q:g}={q_a[q]:g}" for q in QUANTILES))
    print("Quantiles_B: " + ", ".join(f"{q:g}={q_b[q]:g}" for q in QUANTILES))
    print(
        f"VERDICT: {verdict} | D_obs={d_obs:.10f} vs claimed={CLAIMED_D_KS:.10f} "
        f"(|diff|={diff_d:.2e}), p={p_val:.6f} vs 1.0"
    )
    print(
        f"SUMMARY: n_A={n_a}, n_B={n_b}, D_ks={d_obs:.10f}, p={p_val:.6f}, "
        f"within-arm noise=({n_ks_a:.6f}, {n_ks_b:.6f}) -> {verdict}."
    )


if __name__ == "__main__":
    main()
