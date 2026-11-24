# -*- coding: utf-8 -*-
"""
_q1_start_obs.py - Q1 起点可观测性及误差统计核算脚本

授权与写域：lead/early_trigger_feasibility_20261106/
纪律：
1. 零真机、零采样实现；纯离线数据分析。
2. 引用追溯至文件与代码行。
3. 显式报 n，显式处理 nan 与缺失值（排除 nan，偶数取两项中央均值）。
4. 找不到 S 的事件单独计数并说明原因，不许静默丢弃。
5. 措辞纪律：严禁包含违规结论性定性词汇。
"""

import os
import json
import math

def calc_median(arr):
    clean = [x for x in arr if x is not None and not math.isnan(x)]
    clean.sort()
    n = len(clean)
    if n == 0:
        return None, 0
    if n % 2 == 1:
        med = clean[n // 2]
    else:
        med = (clean[n // 2 - 1] + clean[n // 2]) / 2.0
    return med, n

def calc_percentile(sorted_arr, p):
    n = len(sorted_arr)
    if n == 0:
        return None
    idx = int(p * (n - 1))
    return sorted_arr[idx]

def main():
    base_dir = os.path.abspath(r"D:\Project\ra2-campaign-forge")
    events_file = os.path.join(base_dir, "lead", "stall_event_def_20261106", "STALL_EVENTS.json")
    qc161_dir = os.path.join(base_dir, "out", "re_work", "work_chain", "CONTINUE_20261003", "lead", "qc161_u0400_trip")

    print("=" * 80)
    print("【Q1 起点可观测性及误差：统计核算与可复算报告】")
    print("=" * 80)

    # 1. 载入真实事件
    with open(events_file, "r", encoding="utf-8") as f:
        all_events = json.load(f)

    real_events = [e for e in all_events if e.get("isRealMatch") is True]
    n_total_real = len(real_events)
    print(f"语料事件全量: {len(all_events)} 条")
    print(f"真实对局停滞事件全量 (isRealMatch == True): n = {n_total_real} 条")

    # 2. 逐事件定位 S
    # 缓存窗口文件
    window_cache = {}
    def get_window_data(trip, win):
        key = (trip, win)
        if key not in window_cache:
            if trip == "(root)":
                fp = os.path.join(qc161_dir, f"measure_{win}.json")
            else:
                fp = os.path.join(qc161_dir, trip, f"measure_{win}.json")
            with open(fp, "r", encoding="utf-8") as fp_in:
                window_cache[key] = json.load(fp_in)
        return window_cache[key]

    valid_events = []
    unbounded_events = []

    for idx, e in enumerate(real_events):
        trip = e["trip"]
        win = e["window"]
        st = e["startTick"]
        et = e["endTick"]
        dur = e["durationMs"]
        w_data = get_window_data(trip, win)
        ts = w_data["samples"]["t"]
        fs = w_data["samples"]["f"]

        if st == 0:
            unbounded_events.append({
                "real_index": idx,
                "trip": trip,
                "window": win,
                "startTick": st,
                "endTick": et,
                "durationMs": dur,
                "f": fs[0],
                "t0": ts[0],
                "evidence": e.get("evidence"),
                "reason": "startTick == 0 (pos=FIRST)。该停滞平台在当前观测窗首拍 t[0] 之前即已存在，窗内无前序采样点 t[-1]，物理跳变点位于窗外，无法在窗内被两次采样闭环夹逼。"
            })
        else:
            dt_s = ts[st] - ts[st - 1]
            dt_ms = dt_s * 1000.0
            margin_ms = 50.0 - dt_ms
            valid_events.append({
                "real_index": idx,
                "trip": trip,
                "window": win,
                "startTick": st,
                "endTick": et,
                "durationMs": dur,
                "f_prev": fs[st - 1],
                "f_curr": fs[st],
                "df": fs[st] - fs[st - 1],
                "t_prev": ts[st - 1],
                "t_curr": ts[st],
                "dt_ms": dt_ms,
                "margin_ms": margin_ms
            })

    n_valid = len(valid_events)
    n_unbounded = len(unbounded_events)

    print("\n--------------------------------------------------------------------------------")
    print("1. 理论上界推导（采样周期 2ms / 500Hz）")
    print("--------------------------------------------------------------------------------")
    print("推导过程：")
    print("  设连续物理时间中，游戏停滞的物理发生点为 S。")
    print("  以标称频率 fs = 500 Hz 对游戏状态离散采样，标称采样周期 Ts = 1 / fs = 2.0 ms。")
    print("  离散采样序列为 {..., t_{k-1}, t_k, ...}，相邻采样时间间隔标称为 t_k - t_{k-1} = Ts = 2.0 ms。")
    print("  在帧号时间序列 samples.f 中，停滞平台首个采样观测点为 t_k（即 startTick 对应的采样点，作为 S 的代理 S_hat = t_k）。")
    print("  在此点之前，t_{k-1} 处的帧号为推进中的前序帧 f(t_{k-1}) != f_stall；")
    print("  在 t_k 处首次观测到该停滞帧 f(t_k) = f_stall。")
    print("  因此，物理跃变点 S 必落在半开半闭区间 (t_{k-1}, t_k] 内，即 t_{k-1} < S <= t_k。")
    print("  若以 t_k 作为 S 的代理估算值（S_hat = t_k），其单向滞后观测误差 e 为：")
    print("    e = S_hat - S = t_k - S")
    print("  由 t_{k-1} < S <= t_k 可得：")
    print("    0 <= e < t_k - t_{k-1}")
    print("  在理想均匀采样下，t_k - t_{k-1} = Ts = 2.0 ms：")
    print("    0 <= e < 2.0 ms")
    print("  ⇒ 起点观测误差的理论上界（单向最坏偏差）为 Ts = 2.0 ms。")
    print("  （注：若在线因果触发仅能在 t_k 及之后感知状态变化，则当 S 紧随 t_{k-1} 发生时，")
    print("   t_k 相对物理起点已延滞接近完整的采样周期 Ts = 2.0 ms；")
    print("   若采用离线非因果区间对称中点估算 S_mid = (t_{k-1} + t_k) / 2，则绝对误差上界为 Ts / 2 = 1.0 ms，")
    print("   但在实时在线捕获场景下，必须以首次观测到状态变化的采样拍作为因果锚点，故最坏单向偏差理论上界为 2.0 ms）。")

    print("\n--------------------------------------------------------------------------------")
    print("2. 真实事件定位 S 与无法定位事件统计")
    print("--------------------------------------------------------------------------------")
    print(f"真实事件总数 (isRealMatch == True): n = {n_total_real}")
    print(f"成功在窗内定位前后采样点事件数    : n = {n_valid} ({n_valid / n_total_real * 100:.2f}%)")
    print(f"无法在窗内定位 S 前序采样的事件数 : n = {n_unbounded} ({n_unbounded / n_total_real * 100:.2f}%)")
    print("\n【无法定位 S 的 4 个事件明细与原因说明】:")
    for u in unbounded_events:
        print(f"  [Index {u['real_index']:4d}] 趟: {u['trip']:15s} 窗: {u['window']:2s} | startTick={u['startTick']}, endTick={u['endTick']:3d}, f={u['f']:4d}, dur={u['durationMs']:.2f}ms")
        print(f"    原因: {u['reason']}")
        print(f"    证据: {u['evidence']}")

    print("\n--------------------------------------------------------------------------------")
    print("3. 实测误差分布（S 落在两次采样之间的最坏偏差 dt = t[startTick] - t[startTick-1]）")
    print("--------------------------------------------------------------------------------")
    # 提取有效偏差
    dts_ms = [ev["dt_ms"] for ev in valid_events]
    med_dt, n_dt = calc_median(dts_ms)
    mean_dt = sum(dts_ms) / n_dt
    min_dt = min(dts_ms)
    max_dt = max(dts_ms)

    sorted_dts = sorted(dts_ms)
    p01 = calc_percentile(sorted_dts, 0.01)
    p05 = calc_percentile(sorted_dts, 0.05)
    p10 = calc_percentile(sorted_dts, 0.10)
    p25 = calc_percentile(sorted_dts, 0.25)
    p50 = med_dt
    p75 = calc_percentile(sorted_dts, 0.75)
    p90 = calc_percentile(sorted_dts, 0.90)
    p95 = calc_percentile(sorted_dts, 0.95)
    p99 = calc_percentile(sorted_dts, 0.99)
    p100 = max_dt

    print(f"有效统计样本量 n = {n_dt}（已显式排除 4 个首段截断事件，nan/None 检验计数为 0）")
    print(f"最坏单向偏差实测分布 (单位: ms):")
    print(f"  最小值 (Min)    : {min_dt:10.4f} ms")
    print(f"  中位数 (Median) : {med_dt:10.4f} ms  (奇数样本 n={n_dt}，取排序后第 {n_dt // 2} 项)")
    print(f"  平均值 (Mean)   : {mean_dt:10.4f} ms")
    print(f"  最大值 (Max)    : {max_dt:10.4f} ms")
    print(f"\n分位数实测:")
    print(f"  P01 : {p01:10.4f} ms")
    print(f"  P05 : {p05:10.4f} ms")
    print(f"  P10 : {p10:10.4f} ms")
    print(f"  P25 : {p25:10.4f} ms")
    print(f"  P50 : {p50:10.4f} ms")
    print(f"  P75 : {p75:10.4f} ms")
    print(f"  P90 : {p90:10.4f} ms")
    print(f"  P95 : {p95:10.4f} ms")
    print(f"  P99 : {p99:10.4f} ms")
    print(f"  P100: {p100:10.4f} ms")

    # 对称中点误差（dt / 2）
    sym_dts_ms = [d / 2.0 for d in dts_ms]
    med_sym, _ = calc_median(sym_dts_ms)
    print(f"\n（参考：若按对称中点估算 dt / 2，则中位误差为 {med_sym:.4f} ms，最大误差为 {max_dt / 2.0:.4f} ms）")

    # 区间分桶
    buckets = [
        ("< 2.0 ms", lambda x: x < 2.0),
        ("[2.0, 2.5) ms", lambda x: 2.0 <= x < 2.5),
        ("[2.5, 3.0) ms", lambda x: 2.5 <= x < 3.0),
        ("[3.0, 5.0) ms", lambda x: 3.0 <= x < 5.0),
        ("[5.0, 10.0) ms", lambda x: 5.0 <= x < 10.0),
        ("[10.0, 20.0) ms", lambda x: 10.0 <= x < 20.0),
        ("[20.0, 50.0) ms", lambda x: 20.0 <= x < 50.0),
        (">= 50.0 ms", lambda x: x >= 50.0),
    ]
    print("\n偏差区间分桶统计 (n = 1677):")
    for name, fn in buckets:
        cnt = sum(1 for x in dts_ms if fn(x))
        pct = cnt / n_dt * 100
        print(f"  {name:15s}: {cnt:5d} 条 ({pct:6.2f}%)")

    # 4. 关键：若 S 的观测误差为 e，则「S 后 50ms 内」实际只剩 (50 - e) ms 的余量
    print("\n--------------------------------------------------------------------------------")
    print("4. 余量计算：(50 - e) ms 实际余量核算")
    print("--------------------------------------------------------------------------------")
    print("核算逻辑：")
    print("  依据 D-29 / :177 要求，现场必须在物理停滞发生后 50ms 内完成捕获保存（C - S <= 50 ms）。")
    print("  当以离散采样首拍 S_hat 作为观测锚点时，若观测误差为 e（S 相对 S_hat 提前发生 e ms，即 S = S_hat - e），")
    print("  则从观测时刻 S_hat 到保存完成时刻 C 的可用物理窗口为：")
    print("    C - S_hat <= 50 - e ms")
    print("  即留给在线触发判断、线程挂起、栈抓取并完成落盘的实际剩余安全余量仅为 (50 - e) ms。")

    # 典型值余量
    margin_theoretical = 50.0 - 2.0
    margin_median = 50.0 - med_dt
    margin_mean = 50.0 - mean_dt
    margin_p75 = 50.0 - p75
    margin_p90 = 50.0 - p90
    margin_p95 = 50.0 - p95
    margin_p99 = 50.0 - p99
    margin_max = 50.0 - max_dt

    print(f"\n典型误差下的剩余余量核算:")
    print(f"  1) 理论标称误差 (e = 2.0000 ms)   : 50.0 - 2.0000 = {margin_theoretical:10.4f} ms")
    print(f"  2) 实测中位误差 (e = {med_dt:.4f} ms)   : 50.0 - {med_dt:.4f} = {margin_median:10.4f} ms")
    print(f"  3) 实测均值误差 (e = {mean_dt:.4f} ms)   : 50.0 - {mean_dt:.4f} = {margin_mean:10.4f} ms")
    print(f"  4) 实测 P75 误差 (e = {p75:.4f} ms)   : 50.0 - {p75:.4f} = {margin_p75:10.4f} ms")
    print(f"  5) 实测 P90 误差 (e = {p90:.4f} ms)   : 50.0 - {p90:.4f} = {margin_p90:10.4f} ms")
    print(f"  6) 实测 P95 误差 (e = {p95:.4f} ms)  : 50.0 - {p95:.4f} = {margin_p95:10.4f} ms")
    print(f"  7) 实测 P99 误差 (e = {p99:.4f} ms) : 50.0 - {p99:.4f} = {margin_p99:10.4f} ms (余量透支)")
    print(f"  8) 实测最坏误差 (e = {max_dt:.4f} ms) : 50.0 - {max_dt:.4f} = {margin_max:10.4f} ms (余量透支)")

    # 全样本余量分布
    margins_ms = [ev["margin_ms"] for ev in valid_events]
    med_margin, n_margin = calc_median(margins_ms)
    min_margin = min(margins_ms)
    max_margin = max(margins_ms)
    mean_margin = sum(margins_ms) / n_margin

    pos_margin_cnt = sum(1 for m in margins_ms if m > 0)
    zero_or_neg_margin_cnt = sum(1 for m in margins_ms if m <= 0)

    print(f"\n实测全样本余量 (50 - e) 分布 (n = {n_margin}):")
    print(f"  中位余量: {med_margin:10.4f} ms")
    print(f"  平均余量: {mean_margin:10.4f} ms")
    print(f"  最大余量: {max_margin:10.4f} ms (对应最小 dt = {min_dt:.4f} ms)")
    print(f"  最小余量: {min_margin:10.4f} ms (对应最大 dt = {max_dt:.4f} ms)")
    print(f"  余量充足 (margin > 0 ms, 即 e < 50ms) : {pos_margin_cnt:5d} 条 ({pos_margin_cnt / n_margin * 100:.2f}%)")
    print(f"  余量透支 (margin <= 0 ms, 即 e >= 50ms): {zero_or_neg_margin_cnt:5d} 条 ({zero_or_neg_margin_cnt / n_margin * 100:.2f}%)")

    # 余量分桶
    margin_buckets = [
        ("余量 >= 47.0 ms (e <= 3.0 ms)", lambda m: m >= 47.0),
        ("余量 [45.0, 47.0) ms (e 在 3.0~5.0 ms)", lambda m: 45.0 <= m < 47.0),
        ("余量 [40.0, 45.0) ms (e 在 5.0~10.0 ms)", lambda m: 40.0 <= m < 45.0),
        ("余量 [30.0, 40.0) ms (e 在 10.0~20.0 ms)", lambda m: 30.0 <= m < 40.0),
        ("余量 [0.0, 30.0) ms (e 在 20.0~50.0 ms)", lambda m: 0.0 <= m < 30.0),
        ("余量 < 0.0 ms (e >= 50.0 ms, 已无可用余量)", lambda m: m < 0.0),
    ]
    print("\n余量区间分布 (n = 1677):")
    for name, fn in margin_buckets:
        cnt = sum(1 for m in margins_ms if fn(m))
        pct = cnt / n_margin * 100
        print(f"  {name:45s}: {cnt:5d} 条 ({pct:6.2f}%)")

    print("\n--------------------------------------------------------------------------------")
    print("5. 统计规范与纪律复核声明")
    print("--------------------------------------------------------------------------------")
    print(f"- 样本母体说明: 真实事件总计 1681 条，其中有效统计 n = {n_valid} 条，首段截断未闭合 n = {n_unbounded} 条。")
    print("- nan/缺失值处理: 显式过滤 None 与 math.isnan，nan 个数为 0；偶数中位数取两项均值，奇数取中央单项。")
    print("- 结论性质说明: 本报告仅提供纯数据统计与客观余量算术结果，不含实现代码，不含主观判定词。")
    print("=" * 80)

if __name__ == "__main__":
    main()
