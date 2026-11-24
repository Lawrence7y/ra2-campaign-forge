import json
from pathlib import Path

P = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r06\W91_approach\out\trip_P3\run.ndjson")
rows = []
with P.open(encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        if d.get("kind") == "sample" and isinstance(d.get("elapsed_ingame_s"), (int, float)):
            rows.append(d)

print(f"samples={len(rows)}  ingame {rows[0]['elapsed_ingame_s']:.3f} .. {rows[-1]['elapsed_ingame_s']:.3f}")

a8 = [d.get("A8ED50") or 0 for d in rows]
first = next((i for i, v in enumerate(a8) if v), None)
print(f"A8ED50 first nonzero idx={first} t={rows[first]['elapsed_ingame_s'] if first else None}")


def rate(seg):
    if len(seg) < 2:
        return None
    wall = (seg[-1]["t_perf_ns"] - seg[0]["t_perf_ns"]) / 1e9
    cpu = seg[-1]["win_cpu_ms"] - seg[0]["win_cpu_ms"]
    return cpu / (wall * 1000) * 100, wall, cpu, len(seg)


A = rows[:first]
B = rows[first:]
for label, seg in (("A 行军", A), ("B 行军+交战", B), ("全程", rows)):
    r = rate(seg)
    if r:
        pct, wall, cpu, n = r
        print(f"  {label:14s} n={n:6d} wall={wall:7.2f}s cpu={cpu:9.1f}ms  rate={pct:6.2f}%")

# 分段
def seg_rate(t0, t1):
    seg = [d for d in rows if t0 <= d["elapsed_ingame_s"] < t1]
    return rate(seg)


print("\n细分：")
for t0, t1, lab in ((0, 10, "A 内 0-10s"), (10, 44, "A 内 10-44s"),
                    (44.5, 104.5, "B 内 44.5-104.5s (交战初期)"),
                    (105, 260, "B 内 105-260s (交战后期)"),
                    (200, 260, "B 内 200-260s (末段)")):
    r = seg_rate(t0, t1)
    if r:
        print(f"  {lab:26s} n={r[3]:6d} wall={r[1]:7.2f}s rate={r[0]:6.2f}%")

# X87E8E0
xs = [d.get("X87E8E0") for d in rows]
ch = sum(1 for i in range(1, len(xs)) if xs[i] != xs[i - 1])
chA = sum(1 for i in range(1, min(first, len(xs))) if xs[i] != xs[i - 1])
print(f"\nX87E8E0: first={xs[0]} last={xs[-1]} changes_total={ch} changes_in_A={chA}")
