# -*- coding: utf-8 -*-
"""§535 Leader 亲算 -- 慢爬 vs 跳过inc：从 wait-trace 逐拍判定真实形态。

只读既有真机数据。零真机、零写入（除 stdout）。

要判定的对立解释：
  H-skip   : 帧号"跳过 inc"——帧号长时间完全不变，然后突然跳（丢帧）。
  H-slow   : 帧号"慢爬"——帧号持续递增，但每个推进的间隔被拉长。
本件用 400Hz 原始拍到的最短间隔判定，两者在时间序列上形态完全不同。
"""
import json
import os

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

for trip in ("l3_1101v4b", "l3_1101v4c", "l3_1101v4d", "l3_1101v4e"):
    p = os.path.join(BASE, trip, "h8_wait_trace.json")
    if not os.path.exists(p):
        print("%s MISSING" % trip)
        continue
    j = json.load(open(p, encoding="utf-8"))
    s = j["samples"]
    print("=" * 78)
    print("%s  n=%d  wait_s=%.3f  verdict=%s" % (trip, j["n"], j.get("wait_s", -1), j.get("verdict")))

    # 逐拍：(t, frame)
    ts = [x[0] for x in s]
    fs = [x[1] for x in s]
    dt = [ts[i + 1] - ts[i] for i in range(len(ts) - 1)]
    dt.sort()
    med = dt[len(dt) // 2] if dt else 0
    print("  拍间隔: median=%.6fs  p99=%.6fs  max=%.6fs  => 拍率 %.2f Hz" % (
        med, dt[int(len(dt) * 0.99)] if dt else 0, dt[-1] if dt else 0,
        (1.0 / med) if med else 0))

    # 帧推进事件：frame 变化处
    edges = []  # (t, frame)
    prev = None
    for t, f in s:
        if prev is None or f != prev:
            edges.append((t, f))
            prev = f
    print("  帧沿数 = %d ; 首帧=%d 末帧=%d 净推进=%d" % (
        len(edges), edges[0][1], edges[-1][1], edges[-1][1] - edges[0][1]))

    # 相邻帧沿间隔
    gaps = [(edges[i + 1][0] - edges[i][0], edges[i + 1][1] - edges[i][1])
            for i in range(len(edges) - 1)]
    if gaps:
        g = sorted(x[0] for x in gaps)
        df1 = [x for x in gaps if x[1] == 1]
        dfm = [x for x in gaps if x[1] > 1]
        print("  帧沿间隔: median=%.4fs p90=%.4fs p99=%.4fs max=%.4fs" % (
            g[len(g) // 2], g[int(len(g) * 0.9)], g[int(len(g) * 0.99)], g[-1]))
        print("  Δf==1 的对: %d (占 %.1f%%) ; Δf>1 的对: %d" % (
            len(df1), 100.0 * len(df1) / len(gaps), len(dfm)))
        if dfm:
            print("  Δf>1 明细（前 10）：")
            for dt_g, df in dfm[:10]:
                print("     Δt=%.4fs  Δf=%d  => %.1f 帧/s" % (dt_g, df, df / dt_g if dt_g else 0))

    # ★ 核心判定：最长"帧号完全不变"的连续时长 vs 最长"推进但慢"的段落
    # 连续不变段
    stall_runs = []
    run_start = 0
    for i in range(1, len(s)):
        if s[i][1] == s[i - 1][1]:
            continue
        if i - 1 > run_start:
            stall_runs.append((ts[run_start], ts[i - 1] - ts[run_start], fs[run_start]))
        run_start = i
    if len(s) - 1 > run_start:
        stall_runs.append((ts[run_start], ts[-1] - ts[run_start], fs[run_start]))
    if stall_runs:
        sl = sorted(x[1] for x in stall_runs)
        print("  帧号完全不变的连续段: %d 段, 最长=%.4fs, p90=%.4fs, 中位=%.4fs" % (
            len(stall_runs), sl[-1], sl[int(len(sl) * 0.9)], sl[len(sl) // 2]))
        print("  最长 5 段：")
        for t0, dur, f in sorted(stall_runs, key=lambda x: -x[1])[:5]:
            print("     t=%8.3fs  dur=%7.4fs  frame=%d" % (t0, dur, f))

    # 整体推进速率
    span = ts[-1] - ts[0]
    print("  整体: %.3fs 内推进 %d 帧 => %.3f 帧/s" % (span, edges[-1][1] - edges[0][1],
                                                (edges[-1][1] - edges[0][1]) / span if span else 0))
    print()
