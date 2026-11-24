# -*- coding: utf-8 -*-
"""Task 4: Calculate correlation coefficients without external libraries."""
import json
import math

with open(r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_ae38d56c/V2/all_windows.json", "r", encoding="utf-8") as f:
    windows = json.load(f)

# Filter: units0 is not None and live_fps is computable
# Question: Does "live_fps 可算" mean live_fps > 0 or live_fps is not None?
# Let's check both sets:
# Set A: live_fps > 0
# Set B: live_fps is not None (including 0.0)
# Also check if pre_fps15 is not None for correlation with pre_fps15!

def pearson_r(x, y):
    n = len(x)
    if n < 2:
        return None
    mx = sum(x) / n
    my = sum(y) / n
    cov = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    var_x = sum((x[i] - mx) ** 2 for i in range(n))
    var_y = sum((y[i] - my) ** 2 for i in range(n))
    if var_x == 0 or var_y == 0:
        return 0.0
    return cov / math.sqrt(var_x * var_y)

def rank_data(vals):
    # handles ties with average rank
    indexed = sorted(enumerate(vals), key=lambda x: x[1])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(indexed):
        j = i
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j
    return ranks

def spearman_rho(x, y):
    if len(x) < 2:
        return None
    rx = rank_data(x)
    ry = rank_data(y)
    return pearson_r(rx, ry)

for label, cond in [
    ("Condition 1: live_fps > 0 and units0 is not None", lambda w: w["live_fps"] is not None and w["live_fps"] > 0 and w["units0"] is not None),
    ("Condition 2: live_fps is not None (incl 0) and units0 is not None", lambda w: w["live_fps"] is not None and w["units0"] is not None),
    ("Condition 3: gate_ok == True and live_fps > 0 and units0 is not None", lambda w: w.get("gate_ok") and w["live_fps"] is not None and w["live_fps"] > 0 and w["units0"] is not None),
    ("Condition 4: verdict == 'ok' and live_fps > 0 and units0 is not None", lambda w: w.get("verdict") == "ok" and w["live_fps"] is not None and w["live_fps"] > 0 and w["units0"] is not None),
]:
    subset = [w for w in windows if cond(w)]
    print("=" * 80)
    print(f"=== {label} (N = {len(subset)}) ===")
    
    # 1. pre_fps15 vs live_fps
    sub_pre = [w for w in subset if w["pre_fps15"] is not None]
    if sub_pre:
        x_pre = [w["pre_fps15"] for w in sub_pre]
        y_live = [w["live_fps"] for w in sub_pre]
        r_pre = pearson_r(x_pre, y_live)
        rho_pre = spearman_rho(x_pre, y_live)
        print(f"  pre_fps15 vs live_fps (n={len(sub_pre)}):")
        print(f"    Pearson r    = {r_pre:+.4f} ({r_pre:.6f})")
        print(f"    Spearman rho = {rho_pre:+.4f} ({rho_pre:.6f})")
    
    # 2. units0 vs live_fps
    x_u = [w["units0"] for w in subset]
    y_live = [w["live_fps"] for w in subset]
    r_u = pearson_r(x_u, y_live)
    rho_u = spearman_rho(x_u, y_live)
    print(f"  units0 vs live_fps (n={len(subset)}):")
    print(f"    Pearson r    = {r_u:+.4f} ({r_u:.6f})")
    print(f"    Spearman rho = {rho_u:+.4f} ({rho_u:.6f})")

    # 3. Within fixed harness versions
    print("\n  -- Within fixed harness versions (units0 vs live_fps) --")
    by_harness = {}
    for w in subset:
        h = w.get("harness_sha16") or "unknown_early"
        if h not in by_harness:
            by_harness[h] = []
        by_harness[h].append(w)
        
    for h, h_wins in sorted(by_harness.items(), key=lambda x: -len(x[1])):
        xu = [w["units0"] for w in h_wins]
        yu = [w["live_fps"] for w in h_wins]
        hr = pearson_r(xu, yu) if len(xu) >= 2 else None
        hrho = spearman_rho(xu, yu) if len(xu) >= 2 else None
        r_str = f"{hr:+.4f}" if hr is not None else "N/A"
        rho_str = f"{hrho:+.4f}" if hrho is not None else "N/A"
        u_vals = sorted(set(xu))
        print(f"    Harness {h:<18} (n={len(h_wins):2d}, units0={u_vals}): Pearson r = {r_str}, Spearman rho = {rho_str}")
