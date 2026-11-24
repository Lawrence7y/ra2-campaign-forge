#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lead 分析：W98 六趟的**逻辑拍间隔**分布（饥饿/停顿代理）。

⚠️ 边界（必须连同数字一起引用）：
  `frame` 字段 = `*(DWORD*)0x00A8ED84`，是 **32 ms 固定节拍的逻辑拍计数器**（标称 31.25 拍/s）。
  **它不是渲染帧、不是显示帧时长、不是 FPS。**
  W86 的 ddraw 限帧通道也只测"限帧放行间隔"，同样**不是显示帧时长**。
  ⇒ 本脚本产出的是「**仿真逻辑拍被拖慢/饿死**」的证据，**不能**用来主张"画面卡"。

方法：
  采样 6 ms，逻辑拍 ~32 ms ⇒ 每拍约 5 个样本。取每个 `frame` 值的**首次出现**时刻为拍边界，
  相邻拍边界之差 / 拍数增量 = 该拍的实际墙钟时长（量化 ±6 ms）。
  长尾（> 34 ms）即"这一拍算得比预算久"。
"""
from __future__ import annotations

import json
from pathlib import Path

W98 = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r08\W98_clean\out")
TRIPS = ["g_idle_r1", "g_idle_r2", "g_near_r1", "g_near_r2", "g_far_r1", "g_far_r2"]
NOMINAL = 31.25
BUDGET_MS = 1000.0 / NOMINAL  # 32.0 ms


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


def tick_intervals(rows):
    """返回 [(t_rel_s, interval_ms, dtick)]"""
    t0 = int(rows[0]["t_perf_ns"])
    prev_f = None
    prev_t = None
    out = []
    for r in rows:
        f = int(r["frame"])
        t = int(r["t_perf_ns"])
        if prev_f is None:
            prev_f, prev_t = f, t
            continue
        if f != prev_f:
            d = f - prev_f
            out.append(((prev_t - t0) / 1e9, (t - prev_t) / 1e6 / max(d, 1), d))
            prev_f, prev_t = f, t
    return out


def pct(xs, p):
    if not xs:
        return float("nan")
    s = sorted(xs)
    k = (len(s) - 1) * p / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def main():
    print("逻辑拍间隔分析（口径：frame = *0x00A8ED84，32 ms 逻辑拍；**非**显示帧）")
    print(f"标称 {NOMINAL} 拍/s，预算 {BUDGET_MS:.1f} ms/拍\n")
    hdr = (f"{'trip':<13}{'拍数':>7}{'拍/s':>8}{'缺额%':>8}"
           f"{'p50':>7}{'p90':>7}{'p99':>8}{'max':>8}"
           f"{'>34ms':>7}{'>50ms':>7}{'>100ms':>8}")
    print(hdr)
    store = {}
    for t in TRIPS:
        rows = load(t)
        iv = tick_intervals(rows)
        if not iv:
            print(f"{t:<13} 无数据")
            continue
        dur = (int(rows[-1]["t_perf_ns"]) - int(rows[0]["t_perf_ns"])) / 1e9
        ticks = sum(x[2] for x in iv)
        rate = ticks / dur
        vals = [x[1] for x in iv]
        n34 = sum(1 for v in vals if v > 34)
        n50 = sum(1 for v in vals if v > 50)
        n100 = sum(1 for v in vals if v > 100)
        store[t] = dict(dur=dur, ticks=ticks, rate=rate, vals=vals, iv=iv)
        print(f"{t:<13}{ticks:>7}{rate:>8.3f}{(1-rate/NOMINAL)*100:>8.2f}"
              f"{pct(vals,50):>7.2f}{pct(vals,90):>7.2f}{pct(vals,99):>8.2f}{max(vals):>8.2f}"
              f"{n34:>7}{n50:>7}{n100:>8}")

    print("\n" + "=" * 96)
    print("格均值（2 趟）")
    print("=" * 96)
    for cell in ("g_idle", "g_near", "g_far"):
        a, b = store.get(f"{cell}_r1"), store.get(f"{cell}_r2")
        if not a or not b:
            continue
        print(f"[{cell}]  拍/s {a['rate']:.3f} / {b['rate']:.3f}   "
              f"均值 {((a['rate']+b['rate'])/2):.3f}   "
              f"p99 {pct(a['vals'],99):.2f} / {pct(b['vals'],99):.2f}   "
              f"max {max(a['vals']):.2f} / {max(b['vals']):.2f}")

    print("\n" + "=" * 96)
    print("最长 5 次停顿（每趟）")
    print("=" * 96)
    for t in TRIPS:
        if t not in store:
            continue
        top = sorted(store[t]["iv"], key=lambda x: -x[1])[:5]
        s = "  ".join(f"{x[1]:.1f}ms@{x[0]:.1f}s" for x in top)
        print(f"  {t:<13} {s}")

    print("\n" + "=" * 96)
    print(">50 ms 拍的时间占比（'算不过来'的拍占总时长）")
    print("=" * 96)
    for t in TRIPS:
        if t not in store:
            continue
        d = store[t]
        excess = sum(v - BUDGET_MS for v in d["vals"] if v > 50)
        print(f"  {t:<13} >50ms 拍数 {sum(1 for v in d['vals'] if v>50):>4}  "
              f"超出预算合计 {excess:>8.1f} ms  = 墙钟的 {excess/1000/d['dur']*100:>6.3f} %")


if __name__ == "__main__":
    main()
