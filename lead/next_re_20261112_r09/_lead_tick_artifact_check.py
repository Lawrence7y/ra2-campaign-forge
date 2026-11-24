#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lead 自查：L7 的"长逻辑拍"是不是**采样器自己卡住**造成的伪迹？

危险点：采样节拍 6 ms，但 W102 记录每趟 `max_gap_ms` 达 106.95–372.94 ms。
若采样器本身停顿 300 ms，那么跨过这个停顿算出的"拍间隔"就会被膨胀成 300 ms，
而引擎其实一直在正常跑。**若不排除，L7 就是伪迹。**

判据：
  对每个 tick 区间 (>50 ms)，取该区间内部相邻采样的最大间隙 `gap_in`。
  · 若 `gap_in` ≈ 该 tick 区间长度 ⇒ **无法区分**（采样器停顿 / 引擎停顿 同形）→ 记 ambiguous
  · 若 `gap_in` 远小于区间长度 ⇒ 采样器一直在跑，**引擎确实没推进** → 记 solid
  另报：每趟"采样器停顿总量"（gap > 20 ms 的超出部分合计），与"长拍超预算合计"比。
"""
from __future__ import annotations

import json
from pathlib import Path

W98 = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r08\W98_clean\out")
TRIPS = ["g_idle_r1", "g_idle_r2", "g_near_r1", "g_near_r2", "g_far_r1", "g_far_r2"]
NOMINAL_MS = 6.0
AMBIG_RATIO = 0.75   # gap_in / tick_interval 超过此比例即视为"无法区分"


def load(trip):
    rows = []
    with (W98 / f"trip_{trip}" / "run.ndjson").open("r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("frame") is None or r.get("t_perf_ns") is None:
                continue
            rows.append(r)
    rows.sort(key=lambda r: int(r["t_perf_ns"]))
    return rows


def main():
    print("采样器伪迹自查：长逻辑拍 vs 采样间隙")
    print(f"（采样目标 {NOMINAL_MS} ms；gap_in/tick_interval >= {AMBIG_RATIO} 判为无法区分）\n")
    for t in TRIPS:
        rows = load(t)
        t0 = int(rows[0]["t_perf_ns"])
        # 逐样本间隙
        gaps = []
        for a, b in zip(rows, rows[1:]):
            gaps.append((int(b["t_perf_ns"]) - int(a["t_perf_ns"])) / 1e6)
        # 采样器停顿总量（gap 超出 2×名义的部分）
        stall_total = sum(g - 2 * NOMINAL_MS for g in gaps if g > 2 * NOMINAL_MS)
        n_stall = sum(1 for g in gaps if g > 2 * NOMINAL_MS)

        # tick 区间
        prev_f, prev_i = None, None
        ticks = []
        for i, r in enumerate(rows):
            f = int(r["frame"])
            if prev_f is None:
                prev_f, prev_i = f, i
            elif f != prev_f:
                dt = (int(r["t_perf_ns"]) - int(rows[prev_i]["t_perf_ns"])) / 1e6
                d = f - prev_f
                inner = gaps[prev_i:i]
                gap_in = max(inner) if inner else 0.0
                ticks.append(dict(t=(int(rows[prev_i]["t_perf_ns"]) - t0) / 1e9,
                                  iv=dt / max(d, 1), gap_in=gap_in, dtick=d))
                prev_f, prev_i = f, i

        long_ticks = [x for x in ticks if x["iv"] > 50.0]
        amb = [x for x in long_ticks if x["iv"] > 0 and x["gap_in"] / x["iv"] >= AMBIG_RATIO]
        solid = [x for x in long_ticks if x not in amb]
        excess = sum(x["iv"] - 32.0 for x in long_ticks)

        print(f"[{t}]")
        print(f"  样本间隙: >12ms 次数={n_stall:>4}   停顿总量={stall_total:>9.1f} ms  "
              f"最大={max(gaps):>7.2f} ms")
        print(f"  长拍(>50ms): 总 {len(long_ticks):>3} 个   其中")
        print(f"      无法区分(采样器可能停顿) = {len(amb):>3}")
        print(f"      可判为引擎未推进        = {len(solid):>3}")
        if solid:
            top = sorted(solid, key=lambda x: -x["iv"])[:4]
            print("      最可信的 4 个: " + "  ".join(
                f"{x['iv']:.1f}ms@{x['t']:.1f}s(gap{x['gap_in']:.1f})" for x in top))
        print(f"  长拍超预算合计 = {excess:>8.1f} ms   采样器停顿总量 = {stall_total:>8.1f} ms   "
              f"=> 可归因给采样器的比例上限 = {min(1.0, stall_total/excess)*100 if excess>0 else 0:>5.1f} %")
        print()


if __name__ == "__main__":
    main()
