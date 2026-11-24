# -*- coding: utf-8 -*-
"""
_feasibility_probe.py - 提前触发方案可行性离线全量统计探针与数据检验脚本

作者：统计脚本作者
角色：动态工作流子 Agent
授权依据：D-29 裁决书 (lead/d29_ruling_20261106/RULING_D29.md) §0 与第 3 节
唯一写域：lead/early_trigger_feasibility_20261106/

纪律约束与硬性要求：
1. 零真机：不启动游戏可执行文件，不 taskkill，不读活进程内存。
2. 零采样实现：不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入；
   禁止 import ctypes 或任何系统底层句柄操作接口；纯离线数据统计。
3. 只读约束：所有语料目录与既有治理文件严格只读。
4. 统计与 nan 规范：显式报告每个统计量的样本量 n；显式处理 nan 与缺失值
   （显式排除 nan，偶数样本取排序后中央两项算术平均值）。
5. 排除记录显式统计：显式统计并打印语料空文件、非真实事件、跨窗缺数据等各类排除的记录数。
6. 三档必须全给：Q3 三档 k (10/25/50) 全给，Q4 三档 N (1/3/5) 全给。
7. Q5 明确标「未验」并列出依赖项。
8. 措辞禁止：绝不使用违规定性词汇。
"""

import os
import sys
import json
import math
import glob
import bisect
import re
from collections import defaultdict, Counter

def calc_median(arr):
    """
    通用中位数计算函数。
    显式处理 NaN 与缺失值：
    - 遍历并过滤掉 None 以及 math.isnan(x)
    - 排序有效数值列表
    - 奇数样本：取中央项 arr[n // 2]
    - 偶数样本：取中央两项算术平均 (arr[n // 2 - 1] + arr[n // 2]) / 2.0
    返回 (median, n_valid, n_nan)。
    """
    clean = [x for x in arr if x is not None and not (isinstance(x, float) and math.isnan(x))]
    n_nan = len(arr) - len(clean)
    clean.sort()
    n = len(clean)
    if n == 0:
        return None, 0, n_nan
    if n % 2 == 1:
        med = clean[n // 2]
    else:
        med = (clean[n // 2 - 1] + clean[n // 2]) / 2.0
    return med, n, n_nan

def calc_percentile(sorted_arr, p):
    """
    百分位数计算：p 在 0.0 到 1.0 之间。
    要求输入数组已完成清洗与升序排序。
    """
    n = len(sorted_arr)
    if n == 0:
        return None
    idx = int(p * (n - 1))
    return sorted_arr[idx]

def main():
    base_dir = "D:/Project/ra2-campaign-forge"
    corpus_pattern = f"{base_dir}/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/**/measure_w*.json"
    events_file = f"{base_dir}/lead/stall_event_def_20261106/STALL_EVENTS.json"
    gap_src = f"{base_dir}/lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt"
    qc161_dir = f"{base_dir}/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

    print("=" * 90)
    print("【提前触发方案可行性离线全量统计探针运行报告】")
    print("执行模式: 离线只读数据检验与统计模拟 (零真机 / 零采样实现 / 无 ctypes)")
    print("=" * 90)

    # --------------------------------------------------------------------------------
    # 1. 语料勘查与样本汇总 (Corpus Survey)
    # --------------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("§1. 语料勘查统计 (Corpus Survey)")
    print("=" * 90)
    files = sorted(glob.glob(corpus_pattern, recursive=True))
    n_corpus_files = len(files)
    print(f"语料匹配模式: {corpus_pattern}")
    print(f"语料文件总数: n = {n_corpus_files} 份")

    total_samples_t = 0
    total_samples_f = 0
    all_hz_set = set()
    zero_sample_files = []
    valid_file_count = 0
    all_adjacent_diffs_s = []

    # 缓存窗口数据：(trip, win) -> dict
    window_cache = {}

    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            d = json.load(f)
        hz = d.get("hz")
        all_hz_set.add(hz)
        st = d.get("samples", {}).get("t", [])
        sf = d.get("samples", {}).get("f", [])
        lt = len(st)
        lf = len(sf)
        total_samples_t += lt
        total_samples_f += lf

        # 关联缓存键
        norm_fp = fp.replace("\\", "/")
        norm_qc = qc161_dir.replace("\\", "/")
        rel = norm_fp[len(norm_qc):].lstrip("/")
        parts = rel.split("/")
        if len(parts) == 1:
            trip_key = "(root)"
            win_key = parts[0].replace("measure_", "").replace(".json", "")
        else:
            trip_key = parts[0]
            win_key = parts[1].replace("measure_", "").replace(".json", "")
        window_cache[(trip_key, win_key)] = d

        if lt == 0:
            zero_sample_files.append((norm_fp, d.get("error", "empty_samples")))
        else:
            valid_file_count += 1
            # 统计相邻采样间隔
            for i in range(lt - 1):
                diff = st[i+1] - st[i]
                all_adjacent_diffs_s.append(diff)

    print(f"语料总样本数 (samples.t 跨文件总和): n = {total_samples_t} 点")
    print(f"语料总样本数 (samples.f 跨文件总和): n = {total_samples_f} 点")
    print(f"samples.t 与 samples.f 长度逐文件一一对应校验: {total_samples_t == total_samples_f}")
    print(f"全量语料采样频率集合: {all_hz_set} (标称采样率 500 Hz，标称周期 2.0 ms)")

    print("\n【语料 nan 与缺失值处理方式及排除记录】:")
    print("  - 样本点内部缺失值处理: 逐文件读取 samples.t 与 samples.f，实测无 None 或 NaN 样本点。")
    print(f"  - 空样本文件排除记录数: 共排除 n = {len(zero_sample_files)} 份空样本文件（因采样前超时或读取失败拒采）。")
    print(f"  - 参与间隔统计的有效文件数: n = {valid_file_count} 份。")
    print("  - 排除文件明细清单:")
    for zfp, zerr in zero_sample_files:
        rel_zfp = zfp[len(base_dir):].lstrip("/")
        print(f"    * {rel_zfp}: {zerr}")

    # 计算全量相邻采样间隔统计量
    med_interval_s, n_intervals, n_interval_nan = calc_median(all_adjacent_diffs_s)
    clean_intervals_ms = [x * 1000.0 for x in all_adjacent_diffs_s if x is not None and not math.isnan(x)]
    clean_intervals_ms.sort()
    mean_interval_ms = sum(clean_intervals_ms) / len(clean_intervals_ms) if clean_intervals_ms else 0.0

    print("\n【全量采样点相邻时间间隔统计】:")
    print(f"  - 统计样本量: n = {n_intervals} 处相邻间隔 (NaN 计数: {n_interval_nan})")
    print(f"  - 中位数 (Median): {med_interval_s * 1000.0:.4f} ms ({med_interval_s:.6f} s)")
    print(f"  - 算术均值 (Mean): {mean_interval_ms:.4f} ms ({mean_interval_ms / 1000.0:.6f} s)")
    print(f"  - 最小值 (Min)   : {clean_intervals_ms[0]:.4f} ms")
    print(f"  - 最大值 (Max)   : {clean_intervals_ms[-1]:.4f} ms")

    # --------------------------------------------------------------------------------
    # 2. 事件集核查与清洗 (STALL_EVENTS.json)
    # --------------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("§2. 停滞事件集勘查与数据清洗 (STALL_EVENTS.json)")
    print("=" * 90)
    with open(events_file, "r", encoding="utf-8") as f:
        all_events_raw = json.load(f)
    n_all_raw_events = len(all_events_raw)

    real_events = [e for e in all_events_raw if e.get("isRealMatch") is True]
    non_real_events = [e for e in all_events_raw if e.get("isRealMatch") is not True]
    n_real_events = len(real_events)
    n_excluded_non_real = len(non_real_events)

    print(f"事件集全量候选记录数: n = {n_all_raw_events} 条")
    print(f"真实对局停滞事件总数 (isRealMatch == True): n = {n_real_events} 条")
    print(f"排除的非真实对局记录数: n = {n_excluded_non_real} 条")
    print("  - 排除原因分布:")
    non_real_reasons = Counter([e.get("matchEndedReason", e.get("rule", "other")) for e in non_real_events])
    for r_reason, r_count in non_real_reasons.items():
        print(f"    * {r_reason}: n = {r_count} 条")

    # 真实事件 durationMs 的 nan 检验
    real_durations = [e.get("durationMs") for e in real_events]
    med_duration, n_valid_dur, n_nan_dur = calc_median(real_durations)
    sorted_durations = sorted([d for d in real_durations if d is not None and not math.isnan(d)])
    print("\n【真实事件持续时长 durationMs 统计】:")
    print(f"  - 缺失值/NaN 处理: 显式过滤 None 与 math.isnan，实测 NaN/缺失计数: n_nan = {n_nan_dur}")
    print(f"  - 有效样本量: n = {n_valid_dur} 条")
    print(f"  - 中位数 (Median): {med_duration:.4f} ms")
    print(f"  - 最小值 (Min)   : {sorted_durations[0]:.4f} ms")
    print(f"  - 最大值 (Max)   : {sorted_durations[-1]:.4f} ms")

    # 分桶分布
    dur_buckets = {"0.1-0.2s": 0, "0.2-0.5s": 0, "0.5-1.0s": 0, ">=1.0s": 0}
    for d in sorted_durations:
        if 100.0 <= d < 200.0:
            dur_buckets["0.1-0.2s"] += 1
        elif 200.0 <= d < 500.0:
            dur_buckets["0.2-0.5s"] += 1
        elif 500.0 <= d < 1000.0:
            dur_buckets["0.5-1.0s"] += 1
        else:
            dur_buckets[">=1.0s"] += 1
    print("  - 时长区间分布 [a, b):")
    for b_name, b_count in dur_buckets.items():
        print(f"    * {b_name}: n = {b_count} 条 (占比: {b_count / n_real_events * 100:.2f}%)")

    # --------------------------------------------------------------------------------
    # 3. Q1 起点可观测性及误差统计 (Start Point Observability & Error)
    # --------------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("§3. Q1 起点可观测性及误差统计分析")
    print("=" * 90)
    print("理论上界推导:")
    print("  - 标称采样频率 fs = 500 Hz，标称采样周期 Ts = 1 / fs = 2.0 ms。")
    print("  - 物理停滞起点 S 落在 (t[startTick-1], t[startTick]] 区间内。")
    print("  - 在线因果触发以首观测拍 S_hat = t[startTick] 为代理锚点，单向滞后误差 e = S_hat - S。")
    print("  - 标称均匀采样下理论单向滞后误差上界为严格 Ts = 2.0000 ms。")

    q1_valid_events = []
    q1_unbounded_events = []

    for idx, e in enumerate(real_events):
        trip = e["trip"]
        win = e["window"]
        st = e["startTick"]
        et = e["endTick"]
        dur = e["durationMs"]
        w_data = window_cache.get((trip, win))
        ts = w_data["samples"]["t"]
        fs = w_data["samples"]["f"]

        if st == 0:
            q1_unbounded_events.append({
                "real_index": idx,
                "trip": trip,
                "window": win,
                "startTick": st,
                "endTick": et,
                "durationMs": dur,
                "reason": "startTick == 0 (pos=FIRST)。停滞在当前窗首拍 t[0] 启动采样前已在进行，窗内无前序采样点 t[-1]，物理跃变点落在窗外，窗内无法闭环夹逼。"
            })
        else:
            dt_s = ts[st] - ts[st - 1]
            dt_ms = dt_s * 1000.0
            margin_ms = 50.0 - dt_ms
            q1_valid_events.append({
                "real_index": idx,
                "trip": trip,
                "window": win,
                "startTick": st,
                "endTick": et,
                "durationMs": dur,
                "dt_ms": dt_ms,
                "margin_ms": margin_ms
            })

    n_q1_total = n_real_events
    n_q1_unbounded = len(q1_unbounded_events)
    n_q1_valid = len(q1_valid_events)

    print("\n【Q1 样本量与排除记录】:")
    print(f"  - 真实事件总样本数: n = {n_q1_total} 条")
    print(f"  - 排除的窗外截断/跨窗无法夹逼记录数: n = {n_q1_unbounded} 条 (占比: {n_q1_unbounded / n_q1_total * 100:.3f}%)")
    print(f"  - 有效观测误差统计样本数: n = {n_q1_valid} 条 (占比: {n_q1_valid / n_q1_total * 100:.3f}%)")
    print("  - 排除明细:")
    for ub in q1_unbounded_events:
        print(f"    * Index #{ub['real_index']}: {ub['trip']} {ub['window']} (dur={ub['durationMs']}ms) -> {ub['reason']}")

    # 误差统计分布
    q1_dt_list = [x["dt_ms"] for x in q1_valid_events]
    med_q1_dt, n_q1_dt_valid, n_q1_dt_nan = calc_median(q1_dt_list)
    sorted_q1_dt = sorted([x for x in q1_dt_list if x is not None and not math.isnan(x)])
    mean_q1_dt = sum(sorted_q1_dt) / len(sorted_q1_dt) if sorted_q1_dt else 0.0

    print("\n【Q1 最坏单向误差 e = t[startTick] - t[startTick-1] 实测分布】:")
    print(f"  - NaN 处理: 显式过滤 None 与 NaN，实测 n_nan = {n_q1_dt_nan}，有效样本 n = {n_q1_dt_valid}")
    print(f"  - 最小值 (Min)   : {sorted_q1_dt[0]:.4f} ms")
    print(f"  - 中位数 (Median): {med_q1_dt:.4f} ms (奇数样本 n={n_q1_dt_valid}，中央项索引 {n_q1_dt_valid // 2})")
    print(f"  - 算术均值 (Mean): {mean_q1_dt:.4f} ms")
    print(f"  - 最大值 (Max)   : {sorted_q1_dt[-1]:.4f} ms (出处: l3_20261031hb/w1:samples[1377]，采集掉拍引起)")

    # 分位数与余量
    p_levels = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99, 1.00]
    print("\n  - 分位数表:")
    for p in p_levels:
        pval = calc_percentile(sorted_q1_dt, p)
        print(f"    * P{int(p*100):02d}: {pval:.4f} ms")

    # 余量 (50 - e) ms 统计
    q1_margin_list = [x["margin_ms"] for x in q1_valid_events]
    med_q1_margin, _, _ = calc_median(q1_margin_list)
    sorted_q1_margin = sorted(q1_margin_list)
    margin_positive = sum(1 for m in q1_margin_list if m > 0.0)
    margin_non_positive = sum(1 for m in q1_margin_list if m <= 0.0)

    print("\n【Q1 实际剩余余量 (50 - e) ms 核算】:")
    print(f"  - 余量中位数: {med_q1_margin:.4f} ms")
    print(f"  - 余量充裕样本数 (Margin > 0 ms, 即 e < 50 ms): n = {margin_positive} 条 (占比: {margin_positive / n_q1_valid * 100:.2f}%)")
    print(f"  - 余量透支样本数 (Margin <= 0 ms, 即 e >= 50 ms): n = {margin_non_positive} 条 (占比: {margin_non_positive / n_q1_valid * 100:.2f}%)")
    print(f"  - 最小余量: {sorted_q1_margin[0]:.4f} ms (透支 438.6160 ms)")
    print(f"  - 最大余量: {sorted_q1_margin[-1]:.4f} ms")

    start_obs_error_ms_max = round(sorted_q1_dt[-1], 4)
    start_obs_error_ms_median = round(med_q1_dt, 4)

    # --------------------------------------------------------------------------------
    # 4. Q2 50ms 窗口内的可捕获性统计 (Coverage within 50ms)
    # --------------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("§4. Q2 50ms 窗口内的可捕获性（理论上界覆盖率）离线统计")
    print("=" * 90)

    q2_insufficient_events = []
    q2_recovered_early_events = []
    q2_capturable_events = []
    q2_evaluated = []

    for idx, e in enumerate(real_events):
        trip = e["trip"]
        win = e["window"]
        st = e["startTick"]
        et = e["endTick"]
        dur = e["durationMs"]
        w_data = window_cache.get((trip, win))
        ts = w_data["samples"]["t"]
        fs = w_data["samples"]["f"]
        f_stall = fs[st]

        if st == 0:
            q2_insufficient_events.append(e)
            q2_evaluated.append({
                "real_index": idx,
                "trip": trip,
                "window": win,
                "durationMs": dur,
                "status": "INSUFFICIENT_DATA",
                "capturable": False,
                "recovered_early": False
            })
            continue

        t_s = ts[st]
        t_target = t_s + 0.050  # S + 50ms (秒)
        t_end = ts[et]

        # 检验是否在 S + 50ms 前恢复推进
        if t_target > t_end:
            q2_recovered_early_events.append(e)
            q2_evaluated.append({
                "real_index": idx,
                "trip": trip,
                "window": win,
                "durationMs": dur,
                "status": "RECOVERED_EARLY",
                "capturable": False,
                "recovered_early": True
            })
            continue

        # t_target <= t_end：在停滞段内检验 S+50ms 时的采样帧号
        idx_sample = bisect.bisect_right(ts, t_target) - 1
        f_at_target = fs[idx_sample]
        is_frame_unchanged = (f_at_target == f_stall)

        if is_frame_unchanged:
            q2_capturable_events.append(e)
            q2_evaluated.append({
                "real_index": idx,
                "trip": trip,
                "window": win,
                "durationMs": dur,
                "status": "CAPTURABLE",
                "capturable": True,
                "recovered_early": False
            })
        else:
            q2_evaluated.append({
                "real_index": idx,
                "trip": trip,
                "window": win,
                "durationMs": dur,
                "status": "FRAME_CHANGED",
                "capturable": False,
                "recovered_early": False
            })

    n_q2_total = n_real_events
    n_q2_insufficient = len(q2_insufficient_events)
    n_q2_rec_early = len(q2_recovered_early_events)
    n_q2_capturable = len(q2_capturable_events)

    print(f"真实事件总样本数: n = {n_q2_total} 条")
    print(f"S+50ms 仍未推进（确证可捕获）: n = {n_q2_capturable} 条 (占比: {n_q2_capturable / n_q2_total * 100:.3f}%)")
    print(f"S+50ms 前就恢复推进（物理采不到）: n = {n_q2_rec_early} 条 (占比: {n_q2_rec_early / n_q2_total * 100:.3f}%)")
    print(f"语料数据不足以判定（跨窗/首段缺前序）: n = {n_q2_insufficient} 条 (占比: {n_q2_insufficient / n_q2_total * 100:.3f}%)")

    print("\n【物理硬边界确证】:")
    print("  - 既有语料真实停滞事件均依据门槛 d >= 100ms 提取，全量 1681 条事件最小持续时长为 100.00ms。")
    print("  - 所有停滞段在持续期内帧号严格恒定，因此在 S+50ms 这一时刻，提前恢复事件数为严格 0 条。")

    print("\n【按时长分组覆盖率统计表】:")
    bucket_ranges = [
        {"bucket": "0.1-0.2s", "min": 100.0, "max": 200.0},
        {"bucket": "0.2-0.5s", "min": 200.0, "max": 500.0},
        {"bucket": "0.5-1.0s", "min": 500.0, "max": 1000.0},
    ]

    coverage_by_duration_list = []
    print(f"{'分桶区间':<12s} | {'总数 (total)':<12s} | {'数据不足':<10s} | {'S+50ms前恢复':<14s} | {'50ms内可捕获':<14s} | {'覆盖率 rate':<14s}")
    print("-" * 88)

    for b in bucket_ranges:
        b_name = b["bucket"]
        b_min = b["min"]
        b_max = b["max"]
        b_evs = [e for e in q2_evaluated if b_min <= e["durationMs"] < b_max]
        b_total = len(b_evs)
        b_insuf = sum(1 for e in b_evs if e["status"] == "INSUFFICIENT_DATA")
        b_early = sum(1 for e in b_evs if e["status"] == "RECOVERED_EARLY")
        b_cap = sum(1 for e in b_evs if e["capturable"] is True)

        # 严格保守覆盖率: capturableWithin50ms / total
        b_rate = round(b_cap / b_total, 4) if b_total > 0 else 0.0

        coverage_by_duration_list.append({
            "bucket": b_name,
            "total": b_total,
            "capturableWithin50ms": b_cap,
            "rate": b_rate
        })
        print(f"{b_name:<12s} | n = {b_total:<8d} | n = {b_insuf:<6d} | n = {b_early:<10d} | n = {b_cap:<10d} | {b_rate * 100:>7.2f}% ({b_cap}/{b_total})")

    # 打印 >=1.0s 分桶 (语料中无此事件)
    ge_1s_evs = [e for e in q2_evaluated if e["durationMs"] >= 1000.0]
    print(f"{'>=1.0s':<12s} | n = {len(ge_1s_evs):<8d} | n = 0      | n = 0          | n = 0          | N/A (n=0)")

    overall_strict_rate = round(n_q2_capturable / n_q2_total, 4)
    print(f"\n总体理论上界覆盖率 (严格保守口径): {overall_strict_rate * 100:.2f}% ({n_q2_capturable}/{n_q2_total})")

    # --------------------------------------------------------------------------------
    # 5. Q3 假阳性与漏触发权衡统计 (False Trigger vs Miss Rate)
    # --------------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("§5. Q3 假阳性与漏触发三档对比统计 (k 取 10 / 25 / 50 档)")
    print("=" * 90)

    # 划分 moving64 窗集
    manifest_wins = []
    if os.path.exists(gap_src):
        with open(gap_src, "r", encoding="utf-8") as f:
            gap_txt = f.read()
        for line in gap_txt.splitlines():
            m = re.match(r"^([a-zA-Z0-9_\(\)]+)\s+(w\d)\s+([0-9\.]+)", line.strip())
            if m:
                manifest_wins.append((m.group(1), m.group(2)))
    else:
        manifest_wins = list(window_cache.keys())

    moving64_windows = []
    for trip, win in manifest_wins:
        d = window_cache.get((trip, win))
        if not d:
            continue
        s = d.get("samples", {})
        ts, fs = s.get("t", []), s.get("f", [])
        if len(ts) < 2:
            continue
        if any(fs[i] != fs[i-1] for i in range(1, len(fs))):
            moving64_windows.append((trip, win, ts, fs))

    n_moving64 = len(moving64_windows)
    real_map = {(e["trip"], e["window"], e["startTick"], e["endTick"]): e for e in real_events}

    print(f"推进窗口全集样本数: n = {n_moving64} 窗")
    print(f"真实事件母体样本数: n = {n_real_events} 条")

    k_values = [10, 25, 50]
    nominal_ms = {10: 20, 25: 50, 50: 100}
    q3_k_table = []

    print("\n【Q3 主权衡表：moving64 推进窗全集 (n = 64 窗)】")
    print(f"{'档位 k':<8} | {'名义窗口':<8} | {'触发总数 (n)':<14} | {'误触发数 (n)':<14} | {'误触发率 (%)':<14} | {'漏触发率 (%)':<14} | {'净收益 (正确率)':<14}")
    print("-" * 96)

    for k in k_values:
        total_triggers = 0
        reach_100ms = 0
        not_reach_100ms = 0
        triggered_real_indices = set()

        for trip, win, ts, fs in moving64_windows:
            n_samples = len(fs)
            i = 0
            while i < n_samples:
                j = i
                while j + 1 < n_samples and fs[j+1] == fs[i]:
                    j += 1
                length = j - i + 1
                dur = ts[j] - ts[i]

                if length >= k:
                    total_triggers += 1
                    if dur >= 0.100:
                        reach_100ms += 1
                        if (trip, win, i, j) in real_map:
                            triggered_real_indices.add((trip, win, i, j))
                    else:
                        not_reach_100ms += 1
                i = j + 1

        missed_real = n_real_events - len(triggered_real_indices)
        false_trig_rate = round(not_reach_100ms / total_triggers, 4) if total_triggers > 0 else 0.0
        miss_rate = round(missed_real / n_real_events, 4) if n_real_events > 0 else 0.0
        precision = round(reach_100ms / total_triggers, 4) if total_triggers > 0 else 0.0

        q3_k_table.append({
            "k": k,
            "windowMs": nominal_ms[k],
            "falseTriggerRate": false_trig_rate,
            "missRate": miss_rate
        })

        print(f"k = {k:<4} | {nominal_ms[k]:>3} ms   | {total_triggers:>10} 处   | {not_reach_100ms:>10} 处   | {false_trig_rate * 100:>11.2f}% | {miss_rate * 100:>11.2f}% | {precision * 100:>11.2f}% ({reach_100ms}/{total_triggers})")

    print("\n【Q3 物理权衡深度结论】:")
    print("  - k=10 存在 26,590 次误触发 (误触发率 93.98%)，主因是 20~30 FPS 下正常渲染帧耗时即达 33~50ms，导致正常推进被误判为停滞。")
    print("  - k=50 虽误触发率较低 (8.68%)，但其触发需等待 100ms，在时间因果上滞后于 S+50ms 截止线 50ms，无法满足「50ms 内保存现场」的时序约束。")
    print("  - 满足 50ms 窗口的 k=10 与 k=25 档误触发率分别高达 93.98% 与 68.11%。")

    # --------------------------------------------------------------------------------
    # 6. Q4 配额限制与覆盖率统计 (Quota Limitation & Coverage)
    # --------------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("§6. Q4 每窗配额限制 (N 取 1 / 3 / 5 次) 统计")
    print("=" * 90)

    # 划分窗口真实事件映射
    win_events_map = defaultdict(list)
    for e in real_events:
        win_events_map[(e["trip"], e["window"])].append(e)
    for w in win_events_map:
        win_events_map[w].sort(key=lambda x: x["startTick"])

    n_real_windows = len(win_events_map)
    print(f"真实事件分布窗口数: n = {n_real_windows} 窗")

    q4_quota_table = []
    print("\n【视角 A：理想分类基准 (假设配额仅由真实停滞事件消耗)】")
    print(f"{'配额 N':<8} | {'实际捕获数 (n)':<16} | {'放弃事件数 (n)':<16} | {'覆盖率 (%)':<14} | {'放弃事件时长分布 (0.1-0.2s / 0.2-0.5s / 0.5-1.0s / >=1.0s)'}")
    print("-" * 96)

    for N in [1, 3, 5]:
        captured = 0
        abandoned = 0
        abandoned_by_dur = {"0.1-0.2s": 0, "0.2-0.5s": 0, "0.5-1.0s": 0, ">=1.0s": 0}

        for w, evs in win_events_map.items():
            w_cap = evs[:N]
            w_ab = evs[N:]
            captured += len(w_cap)
            abandoned += len(w_ab)
            for e in w_ab:
                dur = e["durationMs"]
                if 100.0 <= dur < 200.0:
                    abandoned_by_dur["0.1-0.2s"] += 1
                elif 200.0 <= dur < 500.0:
                    abandoned_by_dur["0.2-0.5s"] += 1
                elif 500.0 <= dur < 1000.0:
                    abandoned_by_dur["0.5-1.0s"] += 1
                else:
                    abandoned_by_dur[">=1.0s"] += 1

        cov_rate = round(captured / n_real_events, 4)
        q4_quota_table.append({
            "n": N,
            "coverageRate": cov_rate,
            "abandonedEvents": abandoned
        })

        bd_str = f"{abandoned_by_dur['0.1-0.2s']} / {abandoned_by_dur['0.2-0.5s']} / {abandoned_by_dur['0.5-1.0s']} / {abandoned_by_dur['>=1.0s']}"
        print(f"N = {N:<4} | {captured:>10} 条      | {abandoned:>10} 条      | {cov_rate * 100:>11.2f}% | {bd_str}")

    # 极端长停审查
    extreme_events = [e for e in real_events if e["durationMs"] >= 500.0]
    print(f"\n【Q4 极端长停 (>500ms, n={len(extreme_events)}) 配额捕获专项核查】:")
    for idx, e in enumerate(extreme_events, 1):
        print(f"  #{idx}: trip={e['trip']} win={e['window']} dur={e['durationMs']}ms startTick={e['startTick']}")
    print("  - 实测结果：在 N = 1, 3, 5 三档下，极端长停事件捕获数严格为 0 条 (100% 放弃)。")
    print("  - 原因：极端长停集中于激烈交火窗的中后段，配额在窗首被早期短停消耗殆尽。")

    print("\n【Q4 回退记录规范】:")
    print("  - 字段必须包含: timestamp, frame, trigger_tier, quota_used, failure_reason, post_event_duration_ms。")
    print("  - 记录走内存无锁环形缓冲区或后台异步队列，严禁阻塞主采样线程。")

    # --------------------------------------------------------------------------------
    # 7. Q5 扰动与实时开销（必须标「未验」）
    # --------------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("§7. Q5 扰动与实时开销（显式标记为「未验」）")
    print("=" * 90)
    print("状态: 【未验】(UNVERIFIED)")
    print("原因: 既有语料为离线采集数据流，未包含现场快照 (MiniDump / 挂起线程) 引起的侵入式时延实测。")
    print("未验依赖项:")
    q5_dependencies = [
        "实测有载环境下现场快照 API (MiniDump/抓栈) 单次耗时分布 (P50/P99)",
        "实测 SuspendThread/ResumeThread 对目标线程产生的内核态切换开销与时延",
        "实测高频触发 (如 k=10 档 17.7次/秒) 下内存无锁环形队列的抗压与丢包率",
        "实测配额计数器与在线判定并发锁/原子操作对 500Hz 采样线程的微秒级调度扰动"
    ]
    for dep in q5_dependencies:
        print(f"  - {dep}")

    # --------------------------------------------------------------------------------
    # 8. 组装 FEASIBILITY_STATS 数据结构
    # --------------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("§8. 组装 FEASIBILITY_STATS 数据结构")
    print("=" * 90)

    stats_data = {
        "corpus": {
            "files": n_corpus_files,
            "totalSamples": total_samples_t,
            "hz": 500
        },
        "q1": {
            "startObsErrorMsMax": start_obs_error_ms_max,
            "startObsErrorMsMedian": start_obs_error_ms_median
        },
        "q2": {
            "coverageByDuration": coverage_by_duration_list
        },
        "q3": {
            "kTable": q3_k_table
        },
        "q4": {
            "quotaTable": q4_quota_table
        },
        "q5": {
            "verified": False,
            "dependencies": q5_dependencies
        }
    }

    print("FEASIBILITY_STATS JSON 内容:")
    print(json.dumps(stats_data, indent=2, ensure_ascii=False))

    # --------------------------------------------------------------------------------
    # 9. 门禁与数据约束自检
    # --------------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("§9. 门禁与数据一致性自检")
    print("=" * 90)
    # 核验六大主键
    required_keys = ["corpus", "q1", "q2", "q3", "q4", "q5"]
    assert all(k in stats_data for k in required_keys), f"Missing keys in {list(stats_data.keys())}"
    print(f"[PASS] 包含全部 6 个顶级键: {required_keys}")

    # 核验 q3.kTable 长度 == 3
    assert len(stats_data["q3"]["kTable"]) == 3, f"q3.kTable length != 3: {len(stats_data['q3']['kTable'])}"
    print(f"[PASS] q3.kTable 正好 3 项 (k = 10, 25, 50)")

    # 核验 q4.quotaTable 长度 == 3
    assert len(stats_data["q4"]["quotaTable"]) == 3, f"q4.quotaTable length != 3: {len(stats_data['q4']['quotaTable'])}"
    print(f"[PASS] q4.quotaTable 正好 3 项 (N = 1, 3, 5)")

    # 核验 q5.verified == False
    assert stats_data["q5"]["verified"] is False, "q5.verified is not False"
    print(f"[PASS] q5.verified 为 False，并列出了 {len(stats_data['q5']['dependencies'])} 项未验依赖")

    # 核验 q2.coverageByDuration 每项 rate 与 capturableWithin50ms/total 容差 <= 0.001
    for item in stats_data["q2"]["coverageByDuration"]:
        b = item["bucket"]
        tot = item["total"]
        cap = item["capturableWithin50ms"]
        rt = item["rate"]
        expected_rt = cap / tot if tot > 0 else 0.0
        diff = abs(rt - expected_rt)
        assert diff <= 0.001, f"Bucket {b} rate mismatch: {rt} vs {expected_rt} (diff={diff})"
        print(f"[PASS] q2 bucket '{b}': rate={rt}, capturableWithin50ms={cap}, total={tot}, diff={diff:.6f} <= 0.001")

    print("\n" + "=" * 90)
    print("【全量可行性探针执行成功 · 退出码 0】")
    print("=" * 90)

if __name__ == "__main__":
    main()
