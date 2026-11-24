#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lead 独立复算 W85 对照臂（trip_control_dose1500_static）的 CPU 消耗率与每拍值。

口径：
- 窗口 = 局内 t=30..300 s（按 elapsed_ingame_s）；与 W85 的 "30-300s" 一致。
- FILETIME 通道：Σ win_cpu_ms 增量 / 窗口墙钟。
- cycle 通道：Σ win_cyc_delta / (cyc_per_ms * 墙钟)，cyc_per_ms 用同窗口自标定。
- 每拍口径：把每拍的 cyc_delta 换算成 ms，再看中位 / p95（与历史 1.69 ms 口径对照）。
"""
import json
import statistics
from pathlib import Path

P = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r03\W85_pressure\out\trip_control_dose1500_static\run.ndjson")

rows = []
with P.open(encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        if d.get("kind") != "sample":
            continue
        rows.append(d)

print(f"samples={len(rows)}")


def ingame(d):
    v = d.get("elapsed_ingame_s")
    return v if isinstance(v, (int, float)) else None


win = [d for d in rows if ingame(d) is not None and 30.0 <= ingame(d) <= 300.0]
print(f"window(30..300s) samples={len(win)}")
print(f"  ingame range: {ingame(win[0]):.3f} .. {ingame(win[-1]):.3f}")
wall_s = (win[-1]["t_perf_ns"] - win[0]["t_perf_ns"]) / 1e9
print(f"  wall_s={wall_s:.3f}")

# FILETIME 通道
cpu0, cpu1 = win[0]["win_cpu_ms"], win[-1]["win_cpu_ms"]
cpu_ms = cpu1 - cpu0
print(f"\nFILETIME: cpu {cpu0:.2f} -> {cpu1:.2f} ms, delta={cpu_ms:.2f} ms")
print(f"  rate = {cpu_ms / (wall_s * 1000) * 100:.4f} % single-core")

# cycle 通道（自标定）
cyc_sum = sum(d["win_cyc_delta"] for d in win if d.get("win_cyc_delta"))
cyc_per_ms = cyc_sum / cpu_ms if cpu_ms else None
print(f"\ncycle: sum_delta={cyc_sum:,}  cyc_per_ms(selft)={cyc_per_ms:,.1f}  ({cyc_per_ms/1e6:.3f} GHz)")
print(f"  rate = {cyc_sum / (cyc_per_ms * wall_s * 1000) * 100:.4f} % single-core")

# 每拍口径：只统计 frame 前进的样本
per_tick = []
prev_frame = None
for d in win:
    fr = d.get("frame")
    cd = d.get("win_cyc_delta")
    if fr is None or cd is None:
        continue
    if prev_frame is not None and fr > prev_frame:
        per_tick.append(cd / cyc_per_ms)  # ms per frame advance
    prev_frame = fr
per_tick.sort()
print(f"\nper-frame-advance cycle→ms: n={len(per_tick)}")
if per_tick:
    print(f"  median={statistics.median(per_tick):.4f} ms   p95={per_tick[int(0.95*(len(per_tick)-1))]:.4f} ms   mean={statistics.fmean(per_tick):.4f} ms")
    print(f"  中位 / 32ms 拍 = {statistics.median(per_tick)/32.0*100:.2f} %  （历史口径的'占用率'）")

# 每 6ms 采样周期的 cycle 均值（=线程真实占用）
all_delta = [d["win_cyc_delta"] / cyc_per_ms for d in win if d.get("win_cyc_delta") is not None]
if all_delta:
    print(f"\nper-sample(6ms) cycle→ms: n={len(all_delta)} median={statistics.median(all_delta):.4f} ms")
    print(f"  每 6ms 采样周期占用 = {statistics.median(all_delta)/6.0*100:.2f} %")

# A8ED50
nz = sum(1 for d in win if d.get("A8ED50"))
print(f"\nA8ED50 nonzero in window: {nz}/{len(win)}")
