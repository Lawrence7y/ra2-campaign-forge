import os
import json

TRIPS = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

targets = [
    ("l3_1101v4d", "measure_w0.json"),
    ("l3_1101v4d", "measure_w1.json"),
    ("l3_1101v4d", "measure_w2.json"),
    ("l3_1101v4e", "measure_w0.json"),
    ("l3_1101v4e", "measure_w1.json"),
    ("l3_1101v4e", "measure_w2.json"),
    ("l1c_20261021", "measure_w0.json"),
    ("l1c_20261021", "measure_w1.json"),
    ("l1c_20261021", "measure_w2.json"),
    ("l3_20261031hb", "measure_w0.json"),
    ("l3_20261031hb", "measure_w1.json"),
    ("l3_20261031hb", "measure_w2.json"),
]

for trip, w_name in targets:
    p = os.path.join(TRIPS, trip, w_name)
    with open(p, "r", encoding="utf-8") as fp:
        d = json.load(fp)
    edges = d.get("frame_edges", [])
    f0, t0 = edges[0]
    f1, t1 = edges[-1]
    df = f1 - f0
    dt = t1 - t0
    live_fps = df / dt if dt > 0 else 0
    u0 = d.get("gate", {}).get("units0")
    pre = d.get("gate", {}).get("pre_fps15")
    fps_avg = d.get("stats", {}).get("fps_avg")
    fps_p50 = d.get("stats", {}).get("fps_p50")
    t_clock = d.get("t_clock")
    print(f"{trip}/{w_name}:")
    print(f"  t_clock={t_clock}")
    print(f"  edges: f0={f0}, f1={f1}, df={df}, dt={dt:.4f}s")
    print(f"  live_fps={live_fps:.6f}")
    print(f"  fps_avg={fps_avg}")
    print(f"  fps_p50={fps_p50}")
    print(f"  units0={u0}")
    print(f"  pre_fps15={pre}")
