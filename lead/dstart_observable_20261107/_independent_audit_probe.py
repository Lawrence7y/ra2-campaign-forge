# -*- coding: utf-8 -*-
"""_independent_audit_probe.py - 起点独立复核员专项核验探针.

完全独立从原始语料读取、计算、核对。
不修改任何既有文件。零真机、零采样实现。
"""

import hashlib
import json
import math
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
EV_PATH = (ROOT / "lead/stall_event_def_20261106/STALL_EVENTS.json").resolve()
REPORTED_JSON = (ROOT / "lead/dstart_observable_20261107/S_ESTIMATES.json").resolve()
REPORTED_MD = (ROOT / "lead/dstart_observable_20261107/S_UNCERTAINTY.md").resolve()


def run_audit():
    print("=== 起点独立复核员：开始独立重算与审计 ===")

    # 1. 独立读取原始事件集
    with open(EV_PATH, "r", encoding="utf-8") as f:
        all_events = json.load(f)

    # 统计 isRealMatch
    real_events = [e for e in all_events if e.get("isRealMatch") is True]
    non_real_events = [e for e in all_events if e.get("isRealMatch") is not True]

    print(f"原始事件条数: {len(all_events)}")
    print(f"isRealMatch==True 真实事件数: {len(real_events)}")
    print(f"非真实事件数: {len(non_real_events)}")

    # 2. 检查 startTick == 0 的分布
    real_start0 = [e for e in real_events if e["startTick"] == 0]
    all_start0 = [e for e in all_events if e["startTick"] == 0]
    print(f"真实事件中 startTick == 0 的条数: {len(real_start0)}")
    print(f"全部候选事件中 startTick == 0 的条数: {len(all_start0)}")

    for idx, e in enumerate(real_start0, 1):
        print(f"  真实 startTick=0 [{idx}]: trip={e['trip']}, win={e['window']}, start={e['startTick']}, end={e['endTick']}, dur={e['durationMs']}")

    # 3. 读取已上报的 S_ESTIMATES.json
    with open(REPORTED_JSON, "r", encoding="utf-8") as f:
        reported_estimates = json.load(f)

    reported_by_id = {r["eventId"]: r for r in reported_estimates}
    print(f"上报 S_ESTIMATES.json 记录数: {len(reported_estimates)}")

    # 检查 4 条 startTick == 0 在上报结果中的分类
    print("\n--- 检查 4 条 startTick==0 事件在上报中的 quality ---")
    for e in real_start0:
        ev_id = f"{e['trip']}/{e['window']}/{e['startTick']}/{e['endTick']}"
        rep = reported_by_id.get(ev_id)
        if rep is None:
            print(f"  [ERROR] {ev_id} 未在上报数据中找到！")
        else:
            print(f"  {ev_id}: quality={rep.get('quality')}, priorIntervalMs={rep.get('priorIntervalMs')}, sUncertaintyMs={rep.get('sUncertaintyMs')}")

    # 检查是否有任何 startTick==0 事件被误算成 bounded 或 full
    start0_misclassified = [
        r for r in reported_estimates
        if r["eventId"].split("/")[2] == "0" and r["quality"] != "unknown"
    ]
    print(f"startTick==0 但 quality != 'unknown' 的条目数: {len(start0_misclassified)}")

    # 检查是否有 startTick!=0 但 quality == 'unknown' 的条目
    nonzero_unknown = [
        r for r in reported_estimates
        if r["eventId"].split("/")[2] != "0" and r["quality"] == "unknown"
    ]
    print(f"startTick!=0 但 quality == 'unknown' 的条目数: {len(nonzero_unknown)}")

    # 4. 从原始 measure_w*.json 语料全量独立重算
    window_cache = {}
    indep_estimates = []
    mismatches = []

    for e in real_events:
        trip = e["trip"]
        win = e["window"]
        st = e["startTick"]
        et = e["endTick"]
        dur_ms = e["durationMs"]
        ev_id = f"{trip}/{win}/{st}/{et}"

        k = (trip, win)
        if k not in window_cache:
            if trip == "(root)":
                measure_path = BASE / f"measure_{win}.json"
            else:
                measure_path = BASE / trip / f"measure_{win}.json"
            with open(measure_path, "r", encoding="utf-8") as mf:
                wdata = json.load(mf)
            window_cache[k] = wdata["samples"]

        s = window_cache[k]
        ts = s["t"]
        fs = s["f"]
        t0 = ts[0]

        # 验证原始语料切片索引
        if st == 0:
            first_obs = 0.0
            s_up = 0.0
            s_low = 0.0
            s_unc = 0.0
            prior_int = None
            qual = "unknown"
        else:
            # 真实首拍相对窗口起点毫秒
            first_obs = round((ts[st] - t0) * 1000.0, 3)
            s_up = first_obs
            s_low = round((ts[st - 1] - t0) * 1000.0, 3)
            s_unc = round(s_up - s_low, 3)
            prior_int = s_unc
            if prior_int <= 6.0:
                qual = "full"
            else:
                qual = "bounded"

        indep_rec = {
            "eventId": ev_id,
            "durationMs": dur_ms,
            "firstObservedMs": first_obs,
            "sLowerBoundMs": s_low,
            "sUpperBoundMs": s_up,
            "sUncertaintyMs": s_unc,
            "priorIntervalMs": prior_int,
            "quality": qual,
            "f_st": fs[st],
            "f_prev": fs[st - 1] if st > 0 else None,
            "raw_t_st": ts[st],
            "raw_t_prev": ts[st - 1] if st > 0 else None,
        }
        indep_estimates.append(indep_rec)

        # 与上报值核对
        rep = reported_by_id.get(ev_id)
        if rep is None:
            mismatches.append((ev_id, "Missing in reported"))
        else:
            for field in ["firstObservedMs", "sLowerBoundMs", "sUpperBoundMs", "sUncertaintyMs", "priorIntervalMs", "quality"]:
                val_indep = indep_rec[field]
                val_rep = rep.get(field)
                if val_indep != val_rep:
                    mismatches.append((ev_id, field, val_indep, val_rep))

    print(f"\n--- 全量 1681 条独立重算 vs 上报值核对 ---")
    print(f"不匹配项数: {len(mismatches)}")
    if mismatches:
        for m in mismatches[:10]:
            print(f"  Mismatch: {m}")

    # 统计分类计数
    indep_unknown = [r for r in indep_estimates if r["quality"] == "unknown"]
    indep_bounded = [r for r in indep_estimates if r["quality"] == "bounded"]
    indep_full = [r for r in indep_estimates if r["quality"] == "full"]

    print(f"\n--- 独立分类统计 ---")
    print(f"总数 n: {len(indep_estimates)}")
    print(f"unknownCount: {len(indep_unknown)}")
    print(f"boundedCount: {len(indep_bounded)}")
    print(f"fullCount: {len(indep_full)}")

    # 5. 独立算不确定度的统计量 (valid_uncs n = 1677)
    valid_uncs = sorted([r["sUncertaintyMs"] for r in indep_estimates if r["quality"] != "unknown"])
    n_valid = len(valid_uncs)
    print(f"\n--- 不确定度有效样本数 n = {n_valid} ---")

    # 方法 A: 线性最近秩 int(p * (n - 1)) （上报使用的算法）
    def p_nearest_rank(arr, p):
        idx = int(p * (len(arr) - 1))
        return arr[idx]

    # 方法 B: 线性插值 (numpy 默认方法)
    def p_linear_interp(arr, p):
        idx = p * (len(arr) - 1)
        low = int(math.floor(idx))
        high = int(math.ceil(idx))
        weight = idx - low
        return arr[low] * (1.0 - weight) + arr[high] * weight

    # 方法 C: 标准中位数
    med_val = (valid_uncs[n_valid // 2 - 1] + valid_uncs[n_valid // 2]) / 2.0 if n_valid % 2 == 0 else valid_uncs[n_valid // 2]

    min_val = valid_uncs[0]
    max_val = valid_uncs[-1]
    p50_a = p_nearest_rank(valid_uncs, 0.50)
    p95_a = p_nearest_rank(valid_uncs, 0.95)
    p50_b = p_linear_interp(valid_uncs, 0.50)
    p95_b = p_linear_interp(valid_uncs, 0.95)

    print("分位数对比：")
    print(f"  Min: {min_val:.3f} ms")
    print(f"  Max: {max_val:.3f} ms")
    print(f"  P50 (最近秩 index={int(0.5*(n_valid-1))}): {p50_a:.3f} ms")
    print(f"  P50 (中位数 median): {med_val:.3f} ms")
    print(f"  P50 (线性插值): {p50_b:.3f} ms")
    print(f"  P95 (最近秩 index={int(0.95*(n_valid-1))}): {p95_a:.3f} ms")
    print(f"  P95 (线性插值): {p95_b:.3f} ms")

    # 上报数值对比
    reported_stats = {
        "unknownCount": 4,
        "n": 1681,
        "fullCount": 1495,
        "uncertaintyP95Ms": 35.367,
        "uncertaintyP50Ms": 2.515,
        "boundedCount": 182,
        "uncertaintyMaxMs": 488.616,
    }

    print("\n--- 上报 vs 独立实算 对比表 ---")
    comp = [
        ("n", reported_stats["n"], len(indep_estimates)),
        ("unknownCount", reported_stats["unknownCount"], len(indep_unknown)),
        ("boundedCount", reported_stats["boundedCount"], len(indep_bounded)),
        ("fullCount", reported_stats["fullCount"], len(indep_full)),
        ("uncertaintyP50Ms", reported_stats["uncertaintyP50Ms"], p50_a),
        ("uncertaintyP95Ms", reported_stats["uncertaintyP95Ms"], p95_a),
        ("uncertaintyMaxMs", reported_stats["uncertaintyMaxMs"], max_val),
    ]
    for name, rep_v, indep_v in comp:
        match = "MATCH" if rep_v == indep_v else "DIFF"
        print(f"  {name:20s}: 上报={rep_v:<10} 实算={indep_v:<10} [{match}]")

    # 6. 深入剖析 488.616ms 极值事件 (Sampling Gap vs Engine Stall)
    max_ev = [r for r in indep_estimates if r["sUncertaintyMs"] == max_val][0]
    print(f"\n--- 深入分析 488.616ms 极值事件: {max_ev['eventId']} ---")
    trip, win, st_s, et_s = max_ev["eventId"].split("/")
    st = int(st_s)
    et = int(et_s)
    s = window_cache[(trip, win)]
    ts = s["t"]
    fs = s["f"]

    print(f"  样本周围详情:")
    for i in range(max(0, st - 3), min(len(ts), st + 5)):
        delta_prev = (ts[i] - ts[i - 1]) * 1000.0 if i > 0 else 0.0
        marker = " <-- [st-1]" if i == st - 1 else (" <-- [st (S_obs)]" if i == st else "")
        print(f"    idx={i:5d}: t={ts[i]:.6f}, f={fs[i]:4d}, interval_from_prev={delta_prev:8.3f}ms {marker}")

    stall_span_ms = (ts[et] - ts[st]) * 1000.0
    print(f"  停滞段首拍 st={st}, 末拍 et={et}, 帧号恒定={fs[st]}, 采样点数={et - st + 1}")
    print(f"  停滞段时长: (t[{et}] - t[{st}]) * 1000 = {stall_span_ms:.3f} ms")
    print(f"  st 前一拍推进情况: idx={st-1}, t={ts[st-1]:.6f}, f={fs[st-1]}")
    print(f"  帧推进跳跃: 从帧 {fs[st-1]} 到帧 {fs[st]} (推进了 {fs[st] - fs[st-1]} 帧)")
    print(f"  前序采样间隔: (t[{st}] - t[{st-1}]) * 1000 = {(ts[st] - ts[st-1]) * 1000.0:.3f} ms")


if __name__ == "__main__":
    run_audit()
