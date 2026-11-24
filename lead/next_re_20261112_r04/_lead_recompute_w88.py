#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lead 独立复算 W88 的 C6 vs CTRL_C6（回答目标①的核心数字）。

口径与 W85/W86 一致：
- 分析窗：[0, min(t_end)] 内、局内有效样本（elapsed_ingame_s 非空）
- 主统计量：CPU 消耗率 = Δ(win_cpu_ms) / 墙钟（FILETIME kernel+user）
- cycle 通道交叉核对：ΔΣ(win_cyc_delta) / (自标定 cyc_per_ms × 墙钟)
- 事件锚：A8ED50 首非零 idx / 非零占比；X87E8E0 首次变化 idx / 变化次数
"""
import json
import statistics
from pathlib import Path

OUT = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r04\W88_envelope\out")


def load(trip: str):
    p = OUT / trip / "run.ndjson"
    rows = []
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if d.get("kind") != "sample":
                continue
            rows.append(d)
    return rows


def summarize(trip: str, win_end: float | None = None):
    rows = load(trip)
    ing = [d for d in rows if isinstance(d.get("elapsed_ingame_s"), (int, float))]
    if not ing:
        print(f"{trip}: 无局内样本")
        return None
    t0, t1 = ing[0]["elapsed_ingame_s"], ing[-1]["elapsed_ingame_s"]
    end = min(t1, win_end) if win_end else t1
    win = [d for d in ing if d["elapsed_ingame_s"] <= end]

    wall = (win[-1]["t_perf_ns"] - win[0]["t_perf_ns"]) / 1e9
    cpu_ms = win[-1]["win_cpu_ms"] - win[0]["win_cpu_ms"]
    rate = cpu_ms / (wall * 1000) * 100

    cyc = sum(d["win_cyc_delta"] for d in win if d.get("win_cyc_delta"))
    cyc_per_ms = cyc / cpu_ms if cpu_ms else None
    rate_cyc = cyc / (cyc_per_ms * wall * 1000) * 100 if cyc_per_ms else None

    a8 = [d.get("A8ED50") or 0 for d in win]
    nz = sum(1 for v in a8 if v)
    first_nz = next((i for i, v in enumerate(a8) if v), None)

    xs = [d.get("X87E8E0") for d in win if d.get("X87E8E0") is not None]
    x_changes = sum(1 for i in range(1, len(xs)) if xs[i] != xs[i - 1])
    x_first = next((i for i in range(1, len(xs)) if xs[i] != xs[i - 1]), None)

    r = {
        "trip": trip,
        "n": len(win),
        "ingame_range_s": (round(t0, 3), round(end, 3)),
        "wall_s": round(wall, 3),
        "cpu_ms": round(cpu_ms, 2),
        "rate_pct": round(rate, 3),
        "rate_pct_cycle": round(rate_cyc, 3) if rate_cyc else None,
        "a8ed50_nonzero": f"{nz}/{len(a8)}",
        "a8ed50_nonzero_pct": round(100.0 * nz / len(a8), 2),
        "a8ed50_first_nz_idx": first_nz,
        "x87e8e0_changes": x_changes,
        "x87e8e0_first_change_idx": x_first,
    }
    return r


print("=" * 86)
res = []
for t, end in (("trip_C6", 150.002), ("trip_CTRL_C6", 150.002)):
    r = summarize(t, end)
    if r:
        res.append(r)
        for k, v in r.items():
            print(f"  {k:26s} = {v}")
        print("-" * 86)

if len(res) == 2:
    a, b = res[0]["rate_pct"], res[1]["rate_pct"]
    print(f"\n  C6(交战) {a}%  vs  CTRL_C6(全Guard) {b}%")
    print(f"  比值 = {a / b:.3f}   ⇒ 初估抬升 {100 * (a / b - 1):.1f}%")
    print(f"  （cycle 通道：{res[0]['rate_pct_cycle']}% vs {res[1]['rate_pct_cycle']}%，"
          f"比值 {res[0]['rate_pct_cycle'] / res[1]['rate_pct_cycle']:.3f}）")
