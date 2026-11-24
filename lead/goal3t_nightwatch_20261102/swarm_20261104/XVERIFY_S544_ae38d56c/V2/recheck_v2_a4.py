import os
import glob
import json
import statistics

TRIPS = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

all_files = glob.glob(os.path.join(TRIPS, "measure_w*.json")) + glob.glob(os.path.join(TRIPS, "*", "measure_w*.json"))

trip_windows = {}

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
    if u0 is None:
        continue
    trip_dir = os.path.dirname(f)
    tname = os.path.basename(trip_dir) if trip_dir != TRIPS else "_ROOT_"
    wname = os.path.basename(f)
    
    trip_windows.setdefault(tname, []).append({
        "window": wname,
        "live_fps": live_fps,
        "dt": dt,
        "fps_avg": d.get("stats", {}).get("fps_avg")
    })

# 1. 16 multi-window trips
multi_trips = {k: v for k, v in trip_windows.items() if len(v) >= 2}
print(f"Number of multi-window trips: {len(multi_trips)}")

intra_ranges = {}
fast_ranges = []
slow_ranges = []

for tname, wins in multi_trips.items():
    fps_list = [w["live_fps"] for w in wins]
    r = max(fps_list) - min(fps_list)
    intra_ranges[tname] = r
    m = sum(fps_list) / len(fps_list)
    if m >= 28.0:
        fast_ranges.append(r)
    else:
        slow_ranges.append(r)
    print(f"  {tname:20s}: n_wins={len(wins)}, mean={m:.4f}, range={r:.6f}, fps={[round(x, 4) for x in fps_list]}")

all_intra = list(intra_ranges.values())
median_intra = statistics.median(all_intra)
median_fast = statistics.median(fast_ranges)
median_slow = statistics.median(slow_ranges)

print(f"\nIntra-trip range median: {median_intra:.6f} (N={len(all_intra)})")
print(f"Fast group intra-trip range median: {median_fast:.6f} (N={len(fast_ranges)})")
print(f"Slow group intra-trip range median: {median_slow:.6f} (N={len(slow_ranges)})")

# 2. 34 independent trips means
trip_means = []
for tname, wins in trip_windows.items():
    m = sum(w["live_fps"] for w in wins) / len(wins)
    trip_means.append(m)

print(f"\nTotal independent trips: {len(trip_means)}")
trip_means.sort()
print(f"Min trip mean: {trip_means[0]:.6f}, Max trip mean: {trip_means[-1]:.6f}")
print(f"Total range: {trip_means[-1] - trip_means[0]:.6f}")

pair_diffs = []
for i in range(len(trip_means)):
    for j in range(i + 1, len(trip_means)):
        pair_diffs.append(abs(trip_means[i] - trip_means[j]))

print(f"Total pair diffs: {len(pair_diffs)}")
median_inter = statistics.median(pair_diffs)
print(f"Inter-trip pair diff median: {median_inter:.6f}")
print(f"Ratio (inter / intra): {median_inter / median_intra:.6f}")

# 3. Check l3_1101v4c specifically
v4c_wins = trip_windows["l3_1101v4c"]
print(f"\nl3_1101v4c windows:")
for w in v4c_wins:
    print(f"  {w['window']}: live_fps={w['live_fps']:.6f}, dt={w['dt']:.6f}, fps_avg={w['fps_avg']}")
v4c_fps = [w["live_fps"] for w in v4c_wins]
print(f"  v4c range = {max(v4c_fps) - min(v4c_fps):.6f}")

# 4. Check core slow windows dt and difference between fps_avg and live_fps
check_wins = [
    ("l3_1101v4d", "measure_w0.json"),
    ("l3_1101v4e", "measure_w0.json"),
    ("l1c_20261021", "measure_w0.json"),
    ("l3_20261031hb", "measure_w0.json"),
    ("l3_20261031hb", "measure_w1.json"),
]

print(f"\nCore window duration and |live_fps - fps_avg|:")
for tname, wname in check_wins:
    p = os.path.join(TRIPS, tname, wname)
    with open(p, "r", encoding="utf-8") as fp:
        d = json.load(fp)
    edges = d.get("frame_edges", [])
    f0, t0 = edges[0]
    f1, t1 = edges[-1]
    df = f1 - f0
    dt = t1 - t0
    live_fps = df / dt
    fps_avg = d["stats"]["fps_avg"]
    diff = abs(live_fps - fps_avg)
    print(f"  {tname}/{wname}: dt={dt:.4f}s ({dt/25.0*100:.1f}%), live_fps={live_fps:.6f}, fps_avg={fps_avg:.6f}, diff={diff:.6f}")
