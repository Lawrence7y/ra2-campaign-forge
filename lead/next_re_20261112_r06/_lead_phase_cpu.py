import json

REF = {"C6_combat": (31.0, 33.6), "CTRL_C6_guard": (17.75, 18.10)}


def rate(rows):
    if len(rows) < 2:
        return None
    wall = (rows[-1]["t_perf_ns"] - rows[0]["t_perf_ns"]) / 1e9
    cpu = rows[-1]["win_cpu_ms"] - rows[0]["win_cpu_ms"]
    return cpu / (wall * 1000) * 100, wall, cpu


for trip in ("out/trip_P1/run.ndjson", "out/trip_P2/run.ndjson"):
    rows = [json.loads(l) for l in open(trip, encoding="utf-8") if l.strip()]
    rows = [d for d in rows if d.get("kind") == "sample" and isinstance(d.get("elapsed_ingame_s"), (int, float))]
    a8 = [d.get("A8ED50") or 0 for d in rows]
    first = next((i for i, v in enumerate(a8) if v), None)
    print("=" * 72)
    print(trip)
    if first is None:
        print("  无接触点，无法切相")
        continue
    t_contact = rows[first]["elapsed_ingame_s"]
    A = rows[:first]
    B = rows[first:]
    for label, seg in (("A 纯行军/寻路", A), ("B 行军+交战", B)):
        r = rate(seg)
        if r:
            pct, wall, cpu = r
            print(f"  {label}: n={len(seg):5d}  {wall:6.1f} s  {cpu:8.1f} ms  =>  {pct:6.2f} % 单核")
    print(f"  接触时刻 t={t_contact:.2f} s")
    print(f"  参照: C6(交战) {REF['C6_combat'][0]}-{REF['C6_combat'][1]} %  |  CTRL_C6(全Guard) {REF['CTRL_C6_guard'][0]}-{REF['CTRL_C6_guard'][1]} %")
