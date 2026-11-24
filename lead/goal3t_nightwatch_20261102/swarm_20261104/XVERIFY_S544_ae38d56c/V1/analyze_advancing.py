import os
import glob
import json

base_dir = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

root_files = sorted(glob.glob(os.path.join(base_dir, "measure_w*.json")))
sub_files = sorted(glob.glob(os.path.join(base_dir, "*", "measure_w*.json")))
all_files = root_files + sub_files

advancing_rows = []
non_advancing_rows = []

for p in all_files:
    rel_path = os.path.relpath(p, base_dir).replace("\\", "/")
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
    
    stats = d.get("stats") or {}
    edges = d.get("frame_edges") or []
    samples = d.get("samples") or {}
    t_samples = samples.get("t") or []
    f_samples = samples.get("f") or []
    
    fps_avg = stats.get("fps_avg")
    fps_p50 = stats.get("fps_p50")
    frame_ms_p50 = stats.get("frame_ms_p50")
    logic_frames = stats.get("logic_frames")
    span_s = d.get("span_s")
    
    # Check if advancing:
    # In harness: logic = int(f_b) - int(f_a) > 0
    if logic_frames is not None and logic_frames > 0:
        # It advanced!
        f_first, t_first = edges[0][0], edges[0][1]
        f_last, t_last = edges[-1][0], edges[-1][1]
        live_df = f_last - f_first
        live_dt = t_last - t_first
        live_fps = (live_df / live_dt) if live_dt > 0 else None
        
        # calculate tail stall:
        tail_s = (t_samples[-1] - t_last) if t_samples else 0.0
        
        advancing_rows.append({
            "path": rel_path,
            "logic_frames": logic_frames,
            "span_s": span_s,
            "fps_avg": fps_avg,
            "live_df": live_df,
            "live_dt": live_dt,
            "live_fps": live_fps,
            "fps_p50": fps_p50,
            "frame_ms_p50": frame_ms_p50,
            "tail_s": tail_s,
            "tail_ratio": tail_s / span_s if span_s else 0.0,
            "n_edges": len(edges)
        })
    else:
        non_advancing_rows.append({
            "path": rel_path,
            "logic_frames": logic_frames,
            "note": stats.get("note"),
            "verdict": d.get("verdict"),
            "n_edges": len(edges)
        })

print(f"Total files: {len(all_files)}")
print(f"Advancing windows count: {len(advancing_rows)}")
print(f"Non-advancing windows count: {len(non_advancing_rows)}")

# Check conditions:
# 1. fps_avg < 28 but fps_p50 >= 28
cond_avg_slow_p50_fast = [r for r in advancing_rows if r["fps_avg"] < 28 and r["fps_p50"] >= 28]

# 2. live_fps < 28
cond_live_slow = [r for r in advancing_rows if r["live_fps"] < 28]

# 3. fps_p50 < 28
cond_p50_slow = [r for r in advancing_rows if r["fps_p50"] < 28]

# 4. fps_avg < 28
cond_avg_slow = [r for r in advancing_rows if r["fps_avg"] < 28]

print(f"\n--- Statistics on {len(advancing_rows)} advancing windows ---")
print(f"fps_avg < 28: {len(cond_avg_slow)}")
print(f"live_fps < 28: {len(cond_live_slow)}")
print(f"fps_p50 < 28: {len(cond_p50_slow)}")
print(f"fps_avg < 28 AND fps_p50 >= 28: {len(cond_avg_slow_p50_fast)}")

print("\nList of windows with fps_avg < 28 AND fps_p50 >= 28:")
for i, r in enumerate(cond_avg_slow_p50_fast, 1):
    print(f"{i:2d}. {r['path']:<35} fps_avg={r['fps_avg']:.4f}  live_fps={r['live_fps']:.4f}  fps_p50={r['fps_p50']:.4f}  tail={r['tail_s']:.2f}s ({r['tail_ratio']*100:.1f}%) df={r['logic_frames']}")

print("\n--- Detailed list of all 63 advancing windows ---")
print(f"{'#':<3} {'Path':<35} {'df':<5} {'fps_avg':<9} {'live_fps':<10} {'fps_p50':<9} {'tail(s)':<8} {'tail%':<7}")
for i, r in enumerate(advancing_rows, 1):
    live_str = f"{r['live_fps']:.4f}" if r['live_fps'] is not None else "None"
    p50_str = f"{r['fps_p50']:.4f}" if r['fps_p50'] is not None else "None"
    print(f"{i:<3} {r['path']:<35} {r['logic_frames']:<5} {r['fps_avg']:<9.4f} {live_str:<10} {p50_str:<9} {r['tail_s']:<8.2f} {r['tail_ratio']*100:<7.1f}%")

print("\n--- Non-advancing windows (40 files) breakdown ---")
for r in non_advancing_rows:
    print(f"  {r['path']:<35} logic_frames={r['logic_frames']} verdict={r['verdict']} note={r['note']}")
