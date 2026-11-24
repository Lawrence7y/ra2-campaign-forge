#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量复算 W88 所有 trip 的 CPU 消耗率（Lead 口径），输出一览表。"""
import json
import glob
import os
from pathlib import Path

OUT = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r04\W88_envelope\out")


def summarize(trip_dir: Path, win_end=150.002):
    p = trip_dir / "run.ndjson"
    if not p.exists():
        return None
    rows = []
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if d.get("kind") == "sample" and isinstance(d.get("elapsed_ingame_s"), (int, float)):
                rows.append(d)
    if not rows:
        return None
    win = [d for d in rows if d["elapsed_ingame_s"] <= win_end]
    if len(win) < 2:
        return None
    wall = (win[-1]["t_perf_ns"] - win[0]["t_perf_ns"]) / 1e9
    cpu = win[-1]["win_cpu_ms"] - win[0]["win_cpu_ms"]
    rate = cpu / (wall * 1000) * 100
    a8 = [d.get("A8ED50") or 0 for d in win]
    nz = sum(1 for v in a8 if v)
    xs = [d.get("X87E8E0") for d in win if d.get("X87E8E0") is not None]
    xch = sum(1 for i in range(1, len(xs)) if xs[i] != xs[i - 1])
    return {
        "trip": trip_dir.name,
        "n": len(win),
        "wall_s": round(wall, 1),
        "rate": round(rate, 3),
        "a8_pct": round(100.0 * nz / len(a8), 2),
        "x_changes": xch,
    }


res = []
for d in sorted(OUT.iterdir()):
    if d.is_dir() and d.name.startswith("trip_"):
        r = summarize(d)
        if r:
            res.append(r)

print(f"{'trip':<24}{'n':>7}{'wall_s':>8}{'cpu%':>9}{'A8非零%':>9}{'X87变化':>9}")
for r in res:
    print(f"{r['trip']:<24}{r['n']:>7}{r['wall_s']:>8}{r['rate']:>9}{r['a8_pct']:>9}{r['x_changes']:>9}")

Path(OUT.parent / "LEAD_RECOMPUTE_ALL_ARMS.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("\nwrote LEAD_RECOMPUTE_ALL_ARMS.json")
