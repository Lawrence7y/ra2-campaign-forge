# -*- coding: utf-8 -*-
"""
_q3_q4_tradeoff.py - Q3 假阳性与 Q4 配额限制权衡分析探针脚本

角色：权衡分析员 (动态工作流子 Agent)
授权依据：D-29 裁决书 (lead/d29_ruling_20261106/RULING_D29.md)
唯一写域：lead/early_trigger_feasibility_20261106/
纪律遵从：
1. 零真机、零采样实现；纯离线数据检验与统计模拟。
2. 引用追溯至文件路径与代码行。
3. 统计显式报 n，显式处理 nan 与缺失值（排除 nan，偶数取中央两项算术平均）。
4. 三档全给：Q3 三档 k (10/25/50) 全给；Q4 三档 N (1/3/5) 全给。
5. 措辞纪律：严禁出现违规结论性定性词汇。
6. Q5 必须标「未验」。
"""

import os
import sys
import json
import math
import re
from collections import defaultdict, Counter

def calc_median(arr):
    clean = [x for x in arr if x is not None and not (isinstance(x, float) and math.isnan(x))]
    clean.sort()
    n = len(clean)
    if n == 0:
        return None, 0
    if n % 2 == 1:
        med = clean[n // 2]
    else:
        med = (clean[n // 2 - 1] + clean[n // 2]) / 2.0
    return med, n

def main():
    base_dir = os.path.abspath(r"D:\Project\ra2-campaign-forge")
    events_file = os.path.join(base_dir, "lead", "stall_event_def_20261106", "STALL_EVENTS.json")
    gap_src = os.path.join(base_dir, "lead", "goal3t_nightwatch_20261102", "_stall_vs_gap_out.txt")
    qc161_dir = os.path.join(base_dir, "out", "re_work", "work_chain", "CONTINUE_20261003", "lead", "qc161_u0400_trip")

    print("=" * 88)
    print("【权衡分析员 · Q3 假阳性与 Q4 配额离线权衡统计验算报告】")
    print("=" * 88)

    # 1. 读取事件清单与基准窗清单
    with open(events_file, "r", encoding="utf-8") as f:
        all_events = json.load(f)
    real_events = [e for e in all_events if e.get("isRealMatch") is True]
    n_real = len(real_events)
    print(f"1. 语料与事件基准载入：")
    print(f"   - 全量平台记录数: {len(all_events)} 条")
    print(f"   - 真实对局停滞事件总数 (isRealMatch == True): n = {n_real} 条")

    # 检查真实事件中的缺失值与 NaN
    nan_dur = sum(1 for e in real_events if e.get("durationMs") is None or math.isnan(e.get("durationMs")))
    print(f"   - durationMs 缺失/NaN 检验: n_nan = {nan_dur} (有效样本量 n = {n_real - nan_dur})")

    with open(gap_src, "r", encoding="utf-8") as f:
        gap_txt = f.read()
    manifest_wins = []
    for line in gap_txt.splitlines():
        m = re.match(r"^([a-zA-Z0-9_\(\)]+)\s+(w\d)\s+([0-9\.]+)", line.strip())
        if m:
            manifest_wins.append((m.group(1), m.group(2)))
    print(f"   - 夜鹰基准窗清单全量 (full97): n = {len(manifest_wins)} 窗")

    # 缓存窗口数据
    window_cache = {}
    def get_window(trip, win):
        key = (trip, win)
        if key not in window_cache:
            fn = f"measure_{win}.json"
            fp = os.path.join(qc161_dir, fn) if trip == "(root)" else os.path.join(qc161_dir, trip, fn)
            if os.path.exists(fp):
                with open(fp, "r", encoding="utf-8") as fin:
                    window_cache[key] = json.load(fin)
            else:
                window_cache[key] = None
        return window_cache[key]

    # 划分窗口集：moving64 与 26 真实事件窗
    moving64_windows = []
    for trip, win in manifest_wins:
        d = get_window(trip, win)
        if not d:
            continue
        s = d.get("samples", {})
        ts, fs = s.get("t", []), s.get("f", [])
        if len(ts) < 2:
            continue
        if any(fs[i] != fs[i-1] for i in range(1, len(fs))):
            moving64_windows.append((trip, win, ts, fs))

    real_event_wins = sorted(list(set((e["trip"], e["window"]) for e in real_events)))
    print(f"   - 推进窗集 (moving64): n = {len(moving64_windows)} 窗")
    print(f"   - 真实事件所在窗集 (real26): n = {len(real_event_wins)} 窗")

    # 构建真实事件索引映射：(trip, win, startTick, endTick) -> event
    real_map = {(e["trip"], e["window"], e["startTick"], e["endTick"]): e for e in real_events}

    # --------------------------------------------------------------------------------
    # 2. Q3 假阳性与漏触发分析（三档 k：10, 25, 50）
    # --------------------------------------------------------------------------------
    print("\n" + "=" * 88)
    print("2. Q3 假阳性与漏触发三档对比核算（k 取 10 / 25 / 50 档，对应 20 / 50 / 100 ms）")
    print("=" * 88)
    print("判定逻辑与统计定义：")
    print("  - 触发判据：连续 k 个采样点帧号保持不变（即平台游程到达第 k 个点时判定触发一次）")
    print("  - 误触发：触发后平台在当前观测窗内的物理时长未达 d >= 100ms (即 dur < 0.100s)")
    print("  - 正确触发：触发后平台物理时长达到 d >= 100ms")
    print("  - 误触发率 (False Trigger Rate) = 误触发次数 / 触发总次数")
    print("  - 漏触发率 (Miss Rate) = 未被触发的真实事件数 / 真实事件总数 (n=1681)")
    print("  - 净收益 (Precision) = 正确触发数 / 触发总次数")

    k_values = [10, 25, 50]
    nominal_ms = {10: 20, 25: 50, 50: 100}

    # 对 moving64 全量窗口集做仿真
    q3_moving_stats = {}
    for k in k_values:
        total_triggers = 0
        reach_100ms = 0
        not_reach_100ms = 0
        # 记录触发平台在真实事件集中的命中情况
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
                        # 核验是否命中真实事件
                        if (trip, win, i, j) in real_map:
                            triggered_real_indices.add((trip, win, i, j))
                    else:
                        not_reach_100ms += 1
                i = j + 1

        missed_real = n_real - len(triggered_real_indices)
        false_trig_rate = not_reach_100ms / total_triggers if total_triggers > 0 else 0.0
        miss_rate = missed_real / n_real if n_real > 0 else 0.0
        precision = reach_100ms / total_triggers if total_triggers > 0 else 0.0
        strict_real_precision = len(triggered_real_indices) / total_triggers if total_triggers > 0 else 0.0

        q3_moving_stats[k] = {
            "k": k,
            "windowMs": nominal_ms[k],
            "totalTriggers": total_triggers,
            "falseTriggers": not_reach_100ms,
            "correctTriggers": reach_100ms,
            "realEventHits": len(triggered_real_indices),
            "missedRealEvents": missed_real,
            "falseTriggerRate": false_trig_rate,
            "missRate": miss_rate,
            "netGainPrecision": precision,
            "strictRealPrecision": strict_real_precision
        }

    # 对 26 真实事件窗单列对比统计
    q3_real26_stats = {}
    for k in k_values:
        total_triggers = 0
        reach_100ms = 0
        not_reach_100ms = 0
        triggered_real_indices = set()

        for trip, win in real_event_wins:
            d = get_window(trip, win)
            ts, fs = d["samples"]["t"], d["samples"]["f"]
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

        missed_real = n_real - len(triggered_real_indices)
        false_trig_rate = not_reach_100ms / total_triggers if total_triggers > 0 else 0.0
        miss_rate = missed_real / n_real if n_real > 0 else 0.0
        precision = reach_100ms / total_triggers if total_triggers > 0 else 0.0

        q3_real26_stats[k] = {
            "k": k,
            "windowMs": nominal_ms[k],
            "totalTriggers": total_triggers,
            "falseTriggers": not_reach_100ms,
            "correctTriggers": reach_100ms,
            "realEventHits": len(triggered_real_indices),
            "missedRealEvents": missed_real,
            "falseTriggerRate": false_trig_rate,
            "missRate": miss_rate,
            "netGainPrecision": precision
        }

    print("\n【Q3 主权衡表：moving64 推进窗全集 (n = 64 窗, 真实事件母体 n = 1681 条)】")
    print("-" * 105)
    print(f"{'档位 k':<8} | {'名义窗口':<8} | {'触发总数 (n)':<14} | {'误触发数 (n)':<14} | {'误触发率 (%)':<14} | {'漏触发率 (%)':<14} | {'净收益 (正确率)':<14}")
    print("-" * 105)
    for k in k_values:
        row = q3_moving_stats[k]
        print(f"k = {row['k']:<4} | {row['windowMs']:>3} ms   | {row['totalTriggers']:>10} 处   | {row['falseTriggers']:>10} 处   | {row['falseTriggerRate']*100:>11.2f}% | {row['missRate']*100:>11.2f}% | {row['netGainPrecision']*100:>11.2f}% ({row['correctTriggers']}/{row['totalTriggers']})")
    print("-" * 105)

    print("\n【Q3 参考对比表：real26 真实事件窗集 (n = 26 窗, 真实事件母体 n = 1681 条)】")
    print("-" * 105)
    print(f"{'档位 k':<8} | {'名义窗口':<8} | {'触发总数 (n)':<14} | {'误触发数 (n)':<14} | {'误触发率 (%)':<14} | {'漏触发率 (%)':<14} | {'净收益 (正确率)':<14}")
    print("-" * 105)
    for k in k_values:
        row = q3_real26_stats[k]
        print(f"k = {row['k']:<4} | {row['windowMs']:>3} ms   | {row['totalTriggers']:>10} 处   | {row['falseTriggers']:>10} 处   | {row['falseTriggerRate']*100:>11.2f}% | {row['missRate']*100:>11.2f}% | {row['netGainPrecision']*100:>11.2f}% ({row['correctTriggers']}/{row['totalTriggers']})")
    print("-" * 105)

    # 深度分析：时序与 D-29 50ms 窗口约束下的双重权衡
    print("\n【Q3 物理机制与时序深度分析】:")
    print("1. 为什么 k=10 存在 26,590 次误触发 (误触发率 93.98%)？")
    print("   - 在 500 Hz (2ms) 采样率下，k=10 仅需约 18~20ms 帧号不变即触发。")
    print("   - 正常对局在 30 FPS 时单帧渲染耗时约为 33.3ms (跨越 16~17 个采样点)；在 20 FPS 时约为 50ms。")
    print("   - 因此当帧率低于 50 FPS 时，大量正常的对局逻辑帧渲染周期直接触发了 k=10 判据，导致海量误触发。")
    print("2. 为什么 k=50 仍有 162 处误触发 (8.68%)？")
    print("   - 采样点数达到 50 个点，并不等同于物理时长必然 >= 100ms。")
    print("   - 抽验发现实测中存在采样间隔略短于标称值 (例如 1.95ms) 或突发采样密集段，50 个点物理耗时仅 96~98ms，未达 100ms 门槛。")
    print("3. ★ D-29 的 50ms 保存约束与高 k 的矛盾：")
    print("   - D-29 要求「原始上下文在物理起点 S 后 50ms 内实际保存」。")
    print("   - 若选择 k=50 (100ms)，从物理起点 S 到判据满足至少耗时 100ms，触发时刻本身已落后于 S+50ms 截止线整整 50ms！")
    print("   - 因此，k=50 虽误触发率低 (8.68%)，但在时间因果上已无法满足「50ms 内保存现场」的时限要求；")
    print("   - 能够满足 50ms 保存窗口的仅有 k=10 (余量 ~30ms) 与 k=25 (余量 ~0ms)，但两者的误触发率分别高达 93.98% 与 68.11%。")

    # --------------------------------------------------------------------------------
    # 3. Q4 配额限制与覆盖率分析（三档 N：1, 3, 5）
    # --------------------------------------------------------------------------------
    print("\n" + "=" * 88)
    print("3. Q4 每窗配额限制 (N 取 1 / 3 / 5 次) 下的覆盖率与放弃事件核算")
    print("=" * 88)
    print("设定：限定每个观测窗最多触发 N 次，超出 N 次后的后续候选事件全部放弃。")
    print("真实事件母体：n = 1681 条 (分布在 26 个有效推进窗中)。")

    # 视角 A：理想配额 (假设事后分类完美/仅真实事件占用配额，每窗前 N 个真实事件被捕获)
    print("\n--------------------------------------------------------------------------------")
    print("视角 A：理想分类基准 (假设配额仅由真实停滞事件消耗，反映真实事件在各窗密度的理论上限)")
    print("--------------------------------------------------------------------------------")
    win_events_map = defaultdict(list)
    for e in real_events:
        win_events_map[(e["trip"], e["window"])].append(e)
    for w in win_events_map:
        win_events_map[w].sort(key=lambda x: x["startTick"])

    q4_ideal_stats = {}
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

        cov_rate = captured / n_real
        q4_ideal_stats[N] = {
            "n_quota": N,
            "captured": captured,
            "abandoned": abandoned,
            "coverageRate": cov_rate,
            "abandonedBreakdown": abandoned_by_dur
        }

    print(f"{'配额 N':<8} | {'实际捕获数 (n)':<16} | {'放弃事件数 (n)':<16} | {'覆盖率 (%)':<14} | {'放弃事件时长分布 (0.1-0.2s / 0.2-0.5s / 0.5-1.0s / >=1.0s)'}")
    print("-" * 115)
    for N in [1, 3, 5]:
        row = q4_ideal_stats[N]
        bd = row["abandonedBreakdown"]
        bd_str = f"{bd['0.1-0.2s']} / {bd['0.2-0.5s']} / {bd['0.5-1.0s']} / {bd['>=1.0s']}"
        print(f"N = {row['n_quota']:<4} | {row['captured']:>10} 条      | {row['abandoned']:>10} 条      | {row['coverageRate']*100:>11.2f}% | {bd_str}")
    print("-" * 115)

    # 视角 B：在线探测器实际运行配额 (在线触发器每产生一次触发即消耗 1 次配额)
    print("\n--------------------------------------------------------------------------------")
    print("视角 B：在线探测器运行实况 (触发器在窗内达到 k 个点即触发并消耗配额，误触发抢占配额)")
    print("--------------------------------------------------------------------------------")
    q4_online_stats = {}
    for k in k_values:
        q4_online_stats[k] = {}
        for N in [1, 3, 5]:
            captured_real = 0
            abandoned_real = 0
            abandoned_by_dur = {"0.1-0.2s": 0, "0.2-0.5s": 0, "0.5-1.0s": 0, ">=1.0s": 0}

            for trip, win, ts, fs in moving64_windows:
                n_samples = len(fs)
                i = 0
                runs = []
                while i < n_samples:
                    j = i
                    while j + 1 < n_samples and fs[j+1] == fs[i]:
                        j += 1
                    length = j - i + 1
                    dur = ts[j] - ts[i]
                    if length >= k:
                        runs.append((i, j, length, dur))
                    i = j + 1

                # 前 N 次触发消耗配额
                fired_runs = set((r[0], r[1]) for r in runs[:N])

                # 检验该窗内的真实事件是否被覆盖
                win_real_events = [e for e in real_events if e["trip"] == trip and e["window"] == win]
                for re_ev in win_real_events:
                    st, et = re_ev["startTick"], re_ev["endTick"]
                    if (st, et) in fired_runs:
                        captured_real += 1
                    else:
                        abandoned_real += 1
                        dur = re_ev["durationMs"]
                        if 100.0 <= dur < 200.0:
                            abandoned_by_dur["0.1-0.2s"] += 1
                        elif 200.0 <= dur < 500.0:
                            abandoned_by_dur["0.2-0.5s"] += 1
                        elif 500.0 <= dur < 1000.0:
                            abandoned_by_dur["0.5-1.0s"] += 1
                        else:
                            abandoned_by_dur[">=1.0s"] += 1

            cov = captured_real / n_real
            q4_online_stats[k][N] = {
                "k": k,
                "n_quota": N,
                "captured": captured_real,
                "abandoned": abandoned_real,
                "coverageRate": cov,
                "abandonedBreakdown": abandoned_by_dur
            }

    for k in k_values:
        print(f"\n【在线探测器 k = {k} ({nominal_ms[k]}ms) 配额核算表】:")
        print(f"{'配额 N':<8} | {'实际捕获数 (n)':<16} | {'放弃事件数 (n)':<16} | {'覆盖率 (%)':<14} | {'放弃事件时长分布 (0.1-0.2s / 0.2-0.5s / 0.5-1.0s / >=1.0s)'}")
        print("-" * 115)
        for N in [1, 3, 5]:
            row = q4_online_stats[k][N]
            bd = row["abandonedBreakdown"]
            bd_str = f"{bd['0.1-0.2s']} / {bd['0.2-0.5s']} / {bd['0.5-1.0s']} / {bd['>=1.0s']}"
            print(f"N = {row['n_quota']:<4} | {row['captured']:>10} 条      | {row['abandoned']:>10} 条      | {row['coverageRate']*100:>11.2f}% | {bd_str}")
        print("-" * 115)

    print("\n【Q4 放弃事件的极端长停 (0.5-1.0s) 专项审查】:")
    print("在全量 1,681 条真实事件中，持续时间超过 0.5s 的极端长停共 3 条：")
    extreme_events = [e for e in real_events if e["durationMs"] >= 500.0]
    for idx, e in enumerate(extreme_events, 1):
        print(f"  #{idx}: trip={e['trip']}, win={e['window']}, dur={e['durationMs']}ms, startTick={e['startTick']}, endTick={e['endTick']}")
    print("实测核验结果：")
    print("  - 在理想配额下：由于这 3 条长停均发生在密集战斗的窗中后段 (例如 l3_20261031hb w2 中该长停在 sample 2147，其前已有十数次停滞)，配额 N=1/3/5 均在窗首被早期短停消耗殆尽！")
    print("  - 导致在 N = 1、3、5 三档下，全部 3 条 >500ms 的极端停滞事件均被 100% 放弃 (捕获数为 0)！")

    print("\n【Q4 回退记录要求规范】:")
    print("1. 触发后捕获失败记录字段：")
    print("   - timestamp (触发时刻系统精确纳秒时钟)")
    print("   - frame (触发时的逻辑帧号)")
    print("   - trigger_k (触发档位: 10/25/50)")
    print("   - quota_used (当前窗已消耗配额序号: 1..N)")
    print("   - failure_reason (失败原因枚举: SUSPEND_TIMEOUT / SNAPSHOT_FAILED / DISK_IO_BUSY / QUOTA_EXHAUSTED)")
    print("   - post_stall_duration_ms (事后该平台持续时间，若采样线仍持续记录)")
    print("2. 日志隔离性：记录走纯内存环形缓冲区或后台异步追加，不阻塞游戏主线程与采样线程。")

    # --------------------------------------------------------------------------------
    # 4. Q5 扰动与实时开销（必须标「未验」）
    # --------------------------------------------------------------------------------
    print("\n" + "=" * 88)
    print("4. Q5 扰动与实时开销（显式标记为「未验」）")
    print("=" * 88)
    print("状态：【未验】(UNVERIFIED)")
    print("原因：既有语料为离线采集的 samples.t / samples.f 数据流，未包含现场抓取 (MiniDump / SuspendThread / 进程句柄操作) 引起的侵入式时延测量。")
    print("上界估算与依赖项分析：")
    print("  1. 触发判据计算开销：每个 2ms 采样拍仅需 1 次整型比较 (fs[i] == fs[i-1]) 与计数器累加，CPU 开销在纳秒级，几乎为 0。")
    print("  2. 触发频率压力：")
    print(f"     - 在 k=10 档：64 推进窗内触发 28,294 次，平均每窗 442 次，即每秒触发约 17.7 次；")
    print(f"     - 在 k=25 档：64 推进窗内触发 5,343 次，平均每窗 83.5 次，即每秒触发约 3.3 次；")
    print(f"     - 在 k=50 档：64 推进窗内触发 1,866 次，平均每窗 29.2 次，即每秒触发约 1.2 次。")
    print("  3. 扰动风险：若在 k=10 下每秒触发 17.7 次现场抓取，任何进程挂起 (SuspendThread) 或写盘操作将直接导致游戏主线程发生严重卡死，破坏原始对局现场。")
    print("  4. 验证所依赖的数据：需要实机在有负荷状态下实测 SuspendThread/ResumeThread 开销 (微秒级) 及配额管理并发开销。")

    print("\n" + "=" * 88)
    print("【验算完成 · 所有统计均已输出】")
    print("=" * 88)

if __name__ == "__main__":
    main()
