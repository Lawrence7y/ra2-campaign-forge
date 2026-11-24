# -*- coding: utf-8 -*-
"""步骤6：2:1 台阶的成因 —— 采样间隔对 Δframe 的整数化

假设：§817/§818 的 ms/帧 来自 50 ms 采样器的 **逐区间** 统计，而逐区间 Δframe 只能取整数。
若采样间隔 S、真实帧周期 T，则每区间帧数 x=S/T；逐区间 ms/frame = S/round-ish(x)，
其**中位**只能落在 S/n 的离散梯级上 ⇒ 看起来就是 2:1（S/1 与 S/2）。

本脚本：
 1) 用真实 6 ms 序列，抽稀成 50 ms 序列，复现"逐区间中位"并看是否落到 25.x / 50.x；
 2) 给出理论梯级表（S=50.4，T=10..100）；
 3) 对比同一窗口的三种口径：窗口级 Δt/Δframe、逐区间中位、逐区间均值。
"""
import csv
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w153_common as C

OUT = []
S = 50.4  # 观测到的 50 ms 采样器实际间隔（§817 的 50.4 / 25.3 ⇒ S≈50.4–50.6）


def subsample(rows, step_s):
    """按真实时间抽稀：每 step_s 取第一个 >= 目标时刻的样本"""
    out = [rows[0]]
    target = rows[0]["t"] + step_s
    for s in rows[1:]:
        if s["t"] >= target:
            out.append(s)
            target += step_s
    return out


def window_metrics(series, t0, win=10.0):
    """对一条（已抽稀的）序列，按 10 s 窗口给出三种口径"""
    buck = {}
    for s in series:
        k = int((s["t"] - t0) // win)
        buck.setdefault(k, []).append(s)
    res = {}
    for k, seg in sorted(buck.items()):
        if len(seg) < 3:
            continue
        df_tot = seg[-1]["frame"] - seg[0]["frame"]
        dt_tot = (seg[-1]["t"] - seg[0]["t"]) * 1000.0
        per_iv = []
        df_mix = Counter()
        for a, b in zip(seg, seg[1:]):
            dt = (b["t"] - a["t"]) * 1000.0
            df = b["frame"] - a["frame"]
            if dt > 0:
                df_mix[df] += 1
            if df > 0 and dt > 0:
                per_iv.append(dt / df)
        res[k] = dict(span_s=dt_tot / 1000.0, dframe=df_tot,
                      ms_window=(dt_tot / df_tot) if df_tot > 0 else None,
                      ms_iv_med=C.median(per_iv) if per_iv else None,
                      ms_iv_mean=C.mean(per_iv) if per_iv else None,
                      n_iv=len(per_iv), df_mix=dict(df_mix),
                      a8=C.mean([x["A8ED50"] for x in seg if x["A8ED50"] is not None]))
    return res


TRIPS = [
    r"next_re_20261112_r10\W110_crash\out\trip_scan_near_r1\run.ndjson",
    r"next_re_20261112_r10\W110_crash\out\_archive_close\trip_hunt_near_r1\run.ndjson",
    r"next_re_20261112_r10\W110_crash\out\_archive_dense\trip_dense_near_r1\run.ndjson",
]


def main():
    OUT.append("=== 1. 同一批趟：6 ms 原始 vs 抽稀成 50 ms 的三种口径 ===")
    for rel in TRIPS:
        p = os.path.join(C.ROOT, rel)
        if not os.path.exists(p):
            OUT.append("missing " + rel)
            continue
        rows, meta = C.load_series(p)
        t0 = rows[0]["t"]
        w6 = window_metrics(rows, t0)
        rows50 = subsample(rows, S / 1000.0)
        w50 = window_metrics(rows50, t0)
        OUT.append("")
        OUT.append("--- %s（%d 样本 → 抽稀 50.4ms 后 %d 样本）---" % (meta["trip"], len(rows), len(rows50)))
        OUT.append("  %3s %7s %8s %10s %10s %10s %10s  %s" % (
            "win", "dframe", "a8", "6ms窗口级", "50ms窗口级", "50ms逐区间中位", "50ms逐区间均值", "50ms的Δframe分布"))
        for k in sorted(w6):
            a = w6[k]
            b = w50.get(k)
            if not b:
                continue
            OUT.append("  %3d %7d %8.1f %10.3f %10.3f %14s %12s  %s" % (
                k, a["dframe"], a["a8"] or 0, a["ms_window"],
                b["ms_window"] if b["ms_window"] else -1,
                ("%.2f" % b["ms_iv_med"]) if b["ms_iv_med"] else "-",
                ("%.2f" % b["ms_iv_mean"]) if b["ms_iv_mean"] else "-",
                b["df_mix"]))

    # 2) 理论梯级
    OUT.append("")
    OUT.append("=== 2. 理论梯级：采样间隔 S=%.1f ms，真实帧周期 T ⇒ 逐区间中位 ms/frame ===" % S)
    OUT.append("  （逐区间 Δframe 只能取整；中位落在 S/n 上 ⇒ 阶梯）")
    OUT.append("  %8s %14s %14s" % ("真实T(ms)", "S/T", "逐区间中位报表值"))
    for T in (16, 20, 20.2, 25, 25.2, 28, 31.9, 32.0, 33.6, 33.7, 38.2, 40, 45, 50, 64, 85, 88, 107, 120):
        x = S / T
        # 每区间 Δframe = floor(x) 或 ceil(x)；取"有帧推进的区间"里的中位
        lo = int(x)
        frac = x - lo
        # 中位档位：若 lo>=1，则 n=lo 占比 (1-frac), n=lo+1 占比 frac
        if lo == 0:
            med_n = 1  # 只统计有推进的区间 ⇒ 都是 1
        else:
            med_n = lo if (1 - frac) >= 0.5 else lo + 1
        OUT.append("  %8.1f %14.3f %14.2f" % (T, x, S / med_n))
    OUT.append("")
    OUT.append("  ⇒ 结论：逐区间中位口径下，任何 T > %.1f ms 都被报成 %.1f（天花板）；" % (S / 1.5, S))
    OUT.append("          T ∈ (%.1f, %.1f) 被报成 %.1f；T ∈ (%.1f,%.1f) 报成 %.1f。" % (
        S / 2.5, S / 1.5, S / 2, S / 3.5, S / 2.5, S / 3))
    OUT.append("  ⇒ 所以 25.30 / 50.40 正是 S/2 与 S/1 ⇒ **2:1 台阶 = 采样间隔的整数化**，不是引擎性质。")

    # 3) 天花板效应：把 6 ms 数据里的"真实 ms/frame"映射到 50 ms 口径
    OUT.append("")
    OUT.append("=== 3. 天花板/压缩的定量（用 §784 分桶表的中位值反推会被报成什么）===")
    OUT.append("  %12s %16s %10s" % ("真实 ms/frame", "50ms 口径会报成", "误差"))
    for T in (32.03, 32.85, 38.67, 59.46, 85.09, 88.46):
        x = S / T
        lo = int(x)
        frac = x - lo
        if lo == 0:
            med_n = 1
        else:
            med_n = lo if (1 - frac) >= 0.5 else lo + 1
        rep = S / med_n
        OUT.append("  %12.2f %16.2f %9.1f%%" % (T, rep, 100.0 * (rep - T) / T))

    txt = "\n".join(OUT)
    print(txt)
    C.write_evidence("06_quantum.txt", txt)


if __name__ == "__main__":
    main()
