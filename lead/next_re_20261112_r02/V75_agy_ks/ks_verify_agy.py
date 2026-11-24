#!/usr/bin/env python3
"""Independent verifier for two-sample KS and permutation p-value on NDJSON dframe."""

from bisect import bisect_right
import json
import random
import sys

# Tie/ECDF convention: exact sup_x |F_A(x) - F_B(x)| over all real x using
# right-continuous ECDFs F(x) = count(<= x) / n, WITHOUT a lattice/continuity
# correction. Ties are handled by evaluating only at unique support values via
# bisect_right (or full tie-block sums in permutations), never mid-tie.
PROBS = (0.1, 0.25, 0.5, 0.75, 0.9)
N_PERMS = 2000
SEED = 20261113


def load_dframes(path: str) -> list[int]:
    vals: list[int] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            obj = json.loads(s)
            if isinstance(obj, dict):
                v = obj.get("dframe")
                if type(v) is int:  # excludes bool, float, None, str
                    vals.append(v)
    return vals


def ks_num(sa: list[int], sb: list[int]) -> int:
    """Exact numerator max |count_A(<=x)*n_B - count_B(<=x)*n_A| on unique support."""
    na, nb = len(sa), len(sb)
    max_num = 0
    for x in sorted(set(sa) | set(sb)):
        num = abs(bisect_right(sa, x) * nb - bisect_right(sb, x) * na)
        if num > max_num:
            max_num = num
    return max_num


def ks_stat(a: list[int], b: list[int]) -> float:
    sa, sb = sorted(a), sorted(b)
    return ks_num(sa, sb) / (len(sa) * len(sb))


def perm_pvalue(a: list[int], b: list[int], obs_num: int) -> float:
    na, nb = len(a), len(b)
    pooled = sorted(a + b)
    tie_counts: list[int] = []
    run = 1
    for i in range(1, len(pooled)):
        if pooled[i] == pooled[i - 1]:
            run += 1
        else:
            tie_counts.append(run)
            run = 1
    tie_counts.append(run)
    # Shuffle labels over pre-sorted pooled values: O(n) per iteration, no re-sort.
    rng, labels, ge = random.Random(SEED), [1] * na + [0] * nb, 0
    for _ in range(N_PERMS):
        rng.shuffle(labels)
        ca = cb = idx = max_num = 0
        for c in tie_counts:
            ones = labels[idx] if c == 1 else sum(labels[idx : idx + c])
            ca += ones
            cb += c - ones
            num = abs(ca * nb - cb * na)
            if num > max_num:
                max_num = num
            idx += c
        if max_num >= obs_num:
            ge += 1
    return (ge + 1) / (N_PERMS + 1)


def quantiles(xs: list[int]) -> list[float]:
    n = len(xs)
    out: list[float] = []
    for p in PROBS:
        pos = p * (n - 1)
        lo = int(pos)
        frac = pos - lo
        out.append(xs[lo] * (1.0 - frac) + xs[min(lo + 1, n - 1)] * frac)
    return out


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(f"Usage: {sys.argv[0]} <arm_A.ndjson> <arm_B.ndjson>")
    a, b = load_dframes(sys.argv[1]), load_dframes(sys.argv[2])
    na, nb = len(a), len(b)
    if na == 0 or nb == 0:
        raise SystemExit(f"No usable integer 'dframe' values: n_A={na}, n_B={nb}")
    sa, sb = sorted(a), sorted(b)
    obs_num = ks_num(sa, sb)
    d_ks = obs_num / (na * nb)
    p_val = perm_pvalue(a, b, obs_num)
    n_ks_a = ks_stat(a[: na // 2], a[na // 2 :]) if na >= 2 else float("nan")
    n_ks_b = ks_stat(b[: nb // 2], b[nb // 2 :]) if nb >= 2 else float("nan")
    qa, qb = quantiles(sa), quantiles(sb)
    print(f"n_A = {na}, n_B = {nb}")
    print(f"D_ks = {d_ks:.8f}")
    print(f"p_value = {p_val:.6f}")
    print(f"N_ks_A_halfsplit = {n_ks_a:.8f}")
    print(f"N_ks_B_halfsplit = {n_ks_b:.8f}")
    print(f"quantiles_A {list(PROBS)} = {[round(v, 4) for v in qa]}")
    print(f"quantiles_B {list(PROBS)} = {[round(v, 4) for v in qb]}")
    print(f"summary: n_A={na}, n_B={nb}, D_ks={d_ks:.6f}, p_value={p_val:.6f}, "
          f"N_ks_A_halfsplit={n_ks_a:.6f}, N_ks_B_halfsplit={n_ks_b:.6f}")


if __name__ == "__main__":
    main()
