import os
import glob
import json
import math

base_dir = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

print("=== CHECK 1: File count and structure ===")
root_files = sorted(glob.glob(os.path.join(base_dir, "measure_w*.json")))
sub_files = sorted(glob.glob(os.path.join(base_dir, "*", "measure_w*.json")))
all_files = sorted(glob.glob(os.path.join(base_dir, "**", "measure_w*.json"), recursive=True))

print(f"Root files count: {len(root_files)}")
print(f"Subdir files count: {len(sub_files)}")
print(f"All files count: {len(all_files)}")
assert len(all_files) == len(root_files) + len(sub_files), "Mismatch in file counts!"

# Check advancing vs non-advancing
advancing = []
non_advancing = []

for p in all_files:
    rel = os.path.relpath(p, base_dir).replace("\\", "/")
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
    stats = d.get("stats") or {}
    samples = d.get("samples") or {}
    t_samp = samples.get("t") or []
    f_samp = samples.get("f") or []
    edges = d.get("frame_edges") or []
    
    # Calculate directly from samples
    n_samp = len(t_samp)
    if n_samp < 2:
        non_advancing.append((rel, "samples < 2", stats))
        continue
    
    t_a, f_a = t_samp[0], f_samp[0]
    t_b, f_b = t_samp[-1], f_samp[-1]
    span = t_b - t_a
    logic = int(f_b) - int(f_a)
    
    if logic <= 0 or span <= 0:
        non_advancing.append((rel, f"logic={logic}, span={span}", stats))
        continue
    
    # Recompute frame_edges
    re_edges = []
    prev_f = None
    for t, f_val in zip(t_samp, f_samp):
        fi = int(f_val)
        if prev_f is None or fi != prev_f:
            re_edges.append((fi, t))
            prev_f = fi
    
    # Recompute frame_ms and percentiles
    frame_ms = []
    n_multi = 0
    for (fa, ta), (fb, tb) in zip(re_edges, re_edges[1:]):
        df = fb - fa
        if df == 1:
            frame_ms.append((tb - ta) * 1000.0)
        elif df > 1:
            n_multi += 1
            
    re_fps_avg = logic / span
    re_p50 = None
    re_fps_p50 = None
    if frame_ms:
        sorted_vals = sorted(frame_ms)
        idx = 0.50 * (len(sorted_vals) - 1)
        lo = int(math.floor(idx))
        hi = min(lo + 1, len(sorted_vals) - 1)
        frac = idx - lo
        re_p50 = float(sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac)
        re_fps_p50 = (1000.0 / re_p50) if re_p50 > 0 else None
    
    # Recompute live_fps
    re_live_fps = None
    if len(re_edges) >= 2:
        df_live = re_edges[-1][0] - re_edges[0][0]
        dt_live = re_edges[-1][1] - re_edges[0][1]
        if dt_live > 0:
            re_live_fps = df_live / dt_live
            
    tail_stall = t_samp[-1] - re_edges[-1][1]
    head_stall = re_edges[0][1] - t_samp[0]
    
    pre_fps15 = d.get("pre_fps15") or stats.get("pre_fps15")
    # also check if top-level has pre_fps15
    if pre_fps15 is None and "pre_fps15" in d:
        pre_fps15 = d["pre_fps15"]
        
    advancing.append({
        "rel": rel,
        "logic": logic,
        "span": span,
        "fps_avg": re_fps_avg,
        "fps_p50": re_fps_p50,
        "frame_ms_p50": re_p50,
        "live_fps": re_live_fps,
        "tail_stall": tail_stall,
        "head_stall": head_stall,
        "tail_ratio": tail_stall / span,
        "pre_fps15": pre_fps15,
        "n_samples": n_samp,
        "n_edges": len(re_edges),
        "raw_stats": stats,
        "raw_json": d
    })

print(f"Advancing count: {len(advancing)}")
print(f"Non-advancing count: {len(non_advancing)}")

print("\n=== CHECK 2: Threshold 28.0 fps breakdown ===")
avg_lt_28 = [a for a in advancing if a["fps_avg"] < 28.0]
p50_lt_28 = [a for a in advancing if a["fps_p50"] is not None and a["fps_p50"] < 28.0]
live_lt_28 = [a for a in advancing if a["live_fps"] is not None and a["live_fps"] < 28.0]

print(f"fps_avg < 28: {len(avg_lt_28)}")
print(f"fps_p50 < 28: {len(p50_lt_28)}")
print(f"live_fps < 28: {len(live_lt_28)}")

avg_lt_p50_ge = [a for a in advancing if a["fps_avg"] < 28.0 and a["fps_p50"] is not None and a["fps_p50"] >= 28.0]
print(f"fps_avg < 28 AND fps_p50 >= 28: {len(avg_lt_p50_ge)}")

print("\nDetails of the 14 windows:")
for i, a in enumerate(avg_lt_p50_ge, 1):
    print(f"[{i:2d}] {a['rel']:<35} logic={a['logic']:<4} fps_avg={a['fps_avg']:<8.4f} live={a['live_fps']:<8.4f} p50={a['fps_p50']:<8.4f} tail={a['tail_stall']:<6.2f}s ({a['tail_ratio']*100:<5.1f}%) head={a['head_stall']:<6.2f}s")
