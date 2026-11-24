import json
import math

p = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\archive_T34\measure_w0.json"

with open(p, "r", encoding="utf-8") as f:
    d = json.load(f)

stats = d["stats"]
edges = d["frame_edges"]
samples = d["samples"]
t_list = samples["t"]
f_list = samples["f"]

print(f"Sample count: {len(t_list)}")
span = t_list[-1] - t_list[0]
print(f"Span: {span:.6f}s")
hz = len(t_list) / span
print(f"Hz: {hz:.2f}")

# Check gaps dt > 0.010s
dt_list = [t_list[i+1] - t_list[i] for i in range(len(t_list)-1)]
gaps_gt_10ms = [dt for dt in dt_list if dt > 0.010]
print(f"Gaps > 10ms count: {len(gaps_gt_10ms)}")
total_gap_time = sum(gaps_gt_10ms)
print(f"Total gap time: {total_gap_time:.6f}s")
max_dt = max(dt_list)
print(f"Max dt: {max_dt:.6f}s ({max_dt*1000.0:.3f}ms)")

sorted_dt = sorted(dt_list)
p50_dt = sorted_dt[int(len(sorted_dt)*0.5)]
p99_dt = sorted_dt[int(len(sorted_dt)*0.99)]
print(f"Median dt: {p50_dt:.6f}s ({p50_dt*1000.0:.3f}ms)")
print(f"p99 dt: {p99_dt:.6f}s ({p99_dt*1000.0:.3f}ms)")

print(f"Frame edges count: {len(edges)}")
for i, e in enumerate(edges):
    print(f"  Edge {i}: frame={e[0]}, t={e[1]:.6f}, dt_from_start={e[1]-t_list[0]:.6f}s")

# Check progression
t_start = t_list[0]
t_last_edge = edges[-1][1]
t_end = t_list[-1]
f_first = edges[0][0]
f_last = edges[-1][0]

live_dt = t_last_edge - edges[0][1]
live_df = f_last - f_first
live_fps = live_df / live_dt if live_dt > 0 else 0
tail_stall = t_end - t_last_edge

print(f"First edge t: {edges[0][1]:.6f}, last edge t: {t_last_edge:.6f}")
print(f"Active advance duration (live_dt): {live_dt:.6f}s")
print(f"Active advance frames (live_df): {live_df}")
print(f"Live FPS: {live_fps:.4f}")
print(f"Tail stall duration: {tail_stall:.6f}s ({tail_stall/span*100.0:.2f}%)")
print(f"fps_avg: {stats.get('fps_avg')}")
print(f"fps_p50: {stats.get('fps_p50')}")
print(f"frame_ms_p50: {stats.get('frame_ms_p50')}")
