import os
import glob
import json
import math

base_dir = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

all_files = sorted(glob.glob(os.path.join(base_dir, "**", "measure_w*.json"), recursive=True))

data = []

for p in all_files:
    rel = os.path.relpath(p, base_dir).replace("\\", "/")
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
    stats = d.get("stats") or {}
    samples = d.get("samples") or {}
    t_samp = samples.get("t") or []
    f_samp = samples.get("f") or []
    
    if len(t_samp) < 2:
        continue
    logic = int(f_samp[-1]) - int(f_samp[0])
    span = t_samp[-1] - t_samp[0]
    if logic <= 0 or span <= 0:
        continue
        
    edges = d.get("frame_edges") or []
    live_fps = None
    if len(edges) >= 2:
        live_df = edges[-1][0] - edges[0][0]
        live_dt = edges[-1][1] - edges[0][1]
        if live_dt > 0:
            live_fps = live_df / live_dt
            
    gate = d.get("gate") or {}
    pre_fps15 = gate.get("pre_fps15")
    units0 = gate.get("units0")
    map_sha = d.get("map_sha256")
    
    # window type w0, w1, w2
    w_type = None
    if "measure_w0.json" in rel:
        w_type = "w0"
    elif "measure_w1.json" in rel:
        w_type = "w1"
    elif "measure_w2.json" in rel:
        w_type = "w2"
        
    data.append({
        "rel": rel,
        "w_type": w_type,
        "pre_fps15": pre_fps15,
        "units0": units0,
        "map_sha": map_sha,
        "live_fps": live_fps,
        "fps_avg": stats.get("fps_avg"),
        "fps_p50": stats.get("fps_p50")
    })

print(f"Total advancing with data: {len(data)}")

def pearson_rho(xs, ys):
    assert len(xs) == len(ys)
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x)**2 for x in xs)
    var_y = sum((y - mean_y)**2 for y in ys)
    return cov / math.sqrt(var_x * var_y)

valid_all = [d for d in data if d["pre_fps15"] is not None and d["live_fps"] is not None]
print(f"Valid for correlation: {len(valid_all)}")

xs_all = [d["pre_fps15"] for d in valid_all]
ys_all = [d["live_fps"] for d in valid_all]
rho_all = pearson_rho(xs_all, ys_all)
print(f"rho(pre_fps15, live_fps) ALL (N={len(valid_all)}): {rho_all:.4f}")

for w in ["w0", "w1", "w2"]:
    sub = [d for d in valid_all if d["w_type"] == w]
    if sub:
        rho_sub = pearson_rho([d["pre_fps15"] for d in sub], [d["live_fps"] for d in sub])
        print(f"rho(pre_fps15, live_fps) {w} (N={len(sub)}): {rho_sub:.4f}")

# Check trips sharing pre_fps15
print("\n--- Check trip level sharing of pre_fps15 ---")
trip_groups = {}
for d in valid_all:
    parts = d["rel"].split("/")
    trip = parts[0] if len(parts) > 1 else "root"
    trip_groups.setdefault(trip, []).append(d)

multi_w_trips = {k: v for k, v in trip_groups.items() if len(v) > 1}
print(f"Trips with multiple windows: {len(multi_w_trips)}")
for trip, items in sorted(multi_w_trips.items()):
    pre_vals = [it["pre_fps15"] for it in items]
    same = all(abs(p - pre_vals[0]) < 1e-6 for p in pre_vals)
    print(f"Trip {trip:<20}: {len(items)} windows, pre_fps15 values: {pre_vals}, identical: {same}")

# Check specific trip configs: l1c_20261021, l3_1101v4d, l3_1101v3a
print("\n--- Check specific trip metadata ---")
for trip in ["l1c_20261021", "l3_1101v4d", "l3_1101v3a"]:
    trip_dir = os.path.join(base_dir, trip)
    print(f"\nTrip directory: {trip_dir}")
    w0_path = os.path.join(trip_dir, "measure_w0.json")
    if os.path.exists(w0_path):
        with open(w0_path, "r", encoding="utf-8") as jf:
            content = json.load(jf)
            gate = content.get("gate", {})
            print(f"  units0: {gate.get('units0')}")
            print(f"  map_sha256: {content.get('map_sha256')}")
            print(f"  pre_fps15: {gate.get('pre_fps15')}")
            print(f"  fps_avg: {content.get('stats', {}).get('fps_avg')}")
            print(f"  fps_p50: {content.get('stats', {}).get('fps_p50')}")
            # check script/harness
            for k in ["harness", "driver", "script"]:
                if k in content:
                    print(f"  {k}: {content[k]}")
    # Also check if there are run logs or py files or sh files in trip_dir
    files = os.listdir(trip_dir)
    print("  other files:", [f for f in files if not f.endswith(".png") and not f.endswith(".json")])
