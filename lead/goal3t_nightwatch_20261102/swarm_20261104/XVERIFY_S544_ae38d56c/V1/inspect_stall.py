import json

for path in [
    r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l1_20261023e1\measure_w0.json",
    r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l1_20261023hb\measure_w0.json"
]:
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    print("=" * 60)
    print("File:", path)
    stats = d["stats"]
    edges = d["frame_edges"]
    samples = d["samples"]
    print("span_s:", d.get("span_s"))
    print("stats:", stats)
    print("Edges count:", len(edges))
    for i, e in enumerate(edges):
        print(f"  edge {i}: frame={e[0]}, t={e[1]}")
    # Calculate intervals between edges
    intervals = []
    for i in range(len(edges)-1):
        dt = edges[i+1][1] - edges[i][1]
        df = edges[i+1][0] - edges[i][0]
        intervals.append((df, dt, dt*1000.0))
        print(f"  step {i}->{i+1}: df={df}, dt={dt:.6f}s ({dt*1000.0:.2f}ms)")
