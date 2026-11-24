import os
import glob
import json

base_dir = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

files = sorted(glob.glob(os.path.join(base_dir, "measure_w*.json"))) + sorted(glob.glob(os.path.join(base_dir, "*", "measure_w*.json")))

print(f"Total files: {len(files)}")

results = []

for p in files:
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
    verdict = d.get("verdict")
    note = stats.get("note")
    span_s = d.get("span_s")
    
    # Calculate live_fps:
    # live_fps = (末沿帧号 - 首沿帧号) / (末沿时刻 - 首沿时刻)
    live_fps = None
    live_span = None
    df_edges = None
    if len(edges) >= 2:
        f_first, t_first = edges[0][0], edges[0][1]
        f_last, t_last = edges[-1][0], edges[-1][1]
        df_edges = f_last - f_first
        live_span = t_last - t_first
        if live_span > 0:
            live_fps = df_edges / live_span
    
    # Also check if advancement exists:
    advancing = (logic_frames is not None and logic_frames > 0) or (df_edges is not None and df_edges > 0)
    
    # Check tail stall:
    tail_stall = None
    if t_samples and edges:
        tail_stall = t_samples[-1] - edges[-1][1]
    
    results.append({
        "rel_path": rel_path,
        "advancing": advancing,
        "logic_frames": logic_frames,
        "df_edges": df_edges,
        "span_s": span_s,
        "live_span": live_span,
        "tail_stall": tail_stall,
        "fps_avg": fps_avg,
        "fps_p50": fps_p50,
        "frame_ms_p50": frame_ms_p50,
        "live_fps": live_fps,
        "verdict": verdict,
        "note": note,
        "n_samples": len(t_samples),
        "n_edges": len(edges)
    })

print(f"Total processed: {len(results)}")
adv_count = sum(1 for r in results if r["advancing"])
non_adv_count = sum(1 for r in results if not r["advancing"])
print(f"Advancing windows count: {adv_count}")
print(f"Non-advancing windows count: {non_adv_count}")

# Check differences between logic_frames > 0 and df_edges > 0
for r in results:
    if (r["logic_frames"] or 0) > 0 != (r["df_edges"] or 0) > 0:
        print("MISMATCH:", r["rel_path"], r["logic_frames"], r["df_edges"])

