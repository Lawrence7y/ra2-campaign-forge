import os
import glob
import json
import math

TRIPS = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

def pearson(x, y):
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    vx = sum((xi - mx) ** 2 for xi in x)
    vy = sum((yi - my) ** 2 for yi in y)
    denom = math.sqrt(vx * vy)
    return cov / denom if denom > 0 else 0

def rank(vals):
    # Standard ranking with average for ties
    sorted_idx = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(vals):
        j = i
        while j < len(vals) and vals[sorted_idx[j]] == vals[sorted_idx[i]]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[sorted_idx[k]] = avg_rank
        i = j
    return ranks

def spearman(x, y):
    rx = rank(x)
    ry = rank(y)
    return pearson(rx, ry)

# Collect all windows
all_files = glob.glob(os.path.join(TRIPS, "measure_w*.json")) + glob.glob(os.path.join(TRIPS, "*", "measure_w*.json"))

# Group by trip to check pre_fps15 duplication
trip_windows = {}

windows_all = []
for f in all_files:
    with open(f, "r", encoding="utf-8") as fp:
        d = json.load(fp)
    edges = d.get("frame_edges", [])
    if len(edges) < 2:
        continue
    f0, t0 = edges[0]
    f1, t1 = edges[-1]
    df = f1 - f0
    dt = t1 - t0
    if df <= 0 or dt <= 0:
        continue
    live_fps = df / dt
    
    u0 = d.get("gate", {}).get("units0")
    pre = d.get("gate", {}).get("pre_fps15")
    if u0 is None or pre is None:
        continue
        
    trip_dir = os.path.dirname(f)
    tname = os.path.basename(trip_dir) if trip_dir != TRIPS else "_ROOT_"
    wname = os.path.basename(f)
    
    item = {
        "file": f,
        "trip": tname,
        "window": wname,
        "units0": u0,
        "pre_fps15": pre,
        "live_fps": live_fps,
    }
    windows_all.append(item)
    trip_windows.setdefault(tname, []).append(item)

print(f"Total valid windows with units0 and pre_fps15: {len(windows_all)}")

# Check pre_fps15 duplication in multi-window trips
multi_window_trips = {k: v for k, v in trip_windows.items() if len(v) > 1}
dup_count = 0
for tname, wins in multi_window_trips.items():
    pres = set(w["pre_fps15"] for w in wins)
    if len(pres) == 1:
        dup_count += 1
    else:
        print(f"Trip {tname} has differing pre_fps15: {pres}")

print(f"Multi-window trips count: {len(multi_window_trips)}, identical pre_fps15 across windows: {dup_count}/{len(multi_window_trips)}")

# 1. All N=63
x_pre = [w["pre_fps15"] for w in windows_all]
x_u0 = [w["units0"] for w in windows_all]
y_fps = [w["live_fps"] for w in windows_all]

print(f"\n--- All valid windows (N={len(windows_all)}) ---")
print(f"Pearson r(pre_fps15, live_fps) = {pearson(x_pre, y_fps):.6f}")
print(f"Spearman rho(pre_fps15, live_fps) = {spearman(x_pre, y_fps):.6f}")
print(f"Pearson r(units0, live_fps) = {pearson(x_u0, y_fps):.6f}")
print(f"Spearman rho(units0, live_fps) = {spearman(x_u0, y_fps):.6f}")

# 2. Exclude units0 == 0 (N=60)
win_u0_gt0 = [w for w in windows_all if w["units0"] > 0]
x_pre_gt0 = [w["pre_fps15"] for w in win_u0_gt0]
x_u0_gt0 = [w["units0"] for w in win_u0_gt0]
y_fps_gt0 = [w["live_fps"] for w in win_u0_gt0]

print(f"\n--- units0 > 0 windows (N={len(win_u0_gt0)}) ---")
print(f"Pearson r(pre_fps15, live_fps) = {pearson(x_pre_gt0, y_fps_gt0):.6f}")
print(f"Spearman rho(pre_fps15, live_fps) = {spearman(x_pre_gt0, y_fps_gt0):.6f}")
print(f"Pearson r(units0, live_fps) = {pearson(x_u0_gt0, y_fps_gt0):.6f}")
print(f"Spearman rho(units0, live_fps) = {spearman(x_u0_gt0, y_fps_gt0):.6f}")

# 3. Trip means (N=34)
trip_means = []
for tname, wins in trip_windows.items():
    m_pre = sum(w["pre_fps15"] for w in wins) / len(wins)
    m_u0 = sum(w["units0"] for w in wins) / len(wins)
    m_live = sum(w["live_fps"] for w in wins) / len(wins)
    trip_means.append({"trip": tname, "pre_fps15": m_pre, "units0": m_u0, "live_fps": m_live})

print(f"\n--- Trip means (N={len(trip_means)}) ---")
tm_pre = [m["pre_fps15"] for m in trip_means]
tm_u0 = [m["units0"] for m in trip_means]
tm_fps = [m["live_fps"] for m in trip_means]
print(f"Pearson r(pre_fps15, live_fps) = {pearson(tm_pre, tm_fps):.6f}")
print(f"Spearman rho(pre_fps15, live_fps) = {spearman(tm_pre, tm_fps):.6f}")
print(f"Pearson r(units0, live_fps) = {pearson(tm_u0, tm_fps):.6f}")
print(f"Spearman rho(units0, live_fps) = {spearman(tm_u0, tm_fps):.6f}")

# 4. harness8_v4 within
v4_trips = ["l3_1101v4c", "l3_1101v4d", "l3_1101v4e"]
v4_wins = [w for w in windows_all if w["trip"] in v4_trips]
print(f"\n--- harness8_v4 windows (N={len(v4_wins)}) ---")
v4_u0 = [w["units0"] for w in v4_wins]
v4_fps = [w["live_fps"] for w in v4_wins]
print(f"Pearson r(units0, live_fps) = {pearson(v4_u0, v4_fps):.6f}")
print(f"Spearman rho(units0, live_fps) = {spearman(v4_u0, v4_fps):.6f}")
