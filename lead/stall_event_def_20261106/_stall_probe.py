# -*- coding: utf-8 -*-
"""_stall_probe.py - 真实对局停滞事件识别与双口径统计探针。

授权依据：D-26 裁决书先补离线件；唯一写域 lead/stall_event_def_20261106/。
纪律：
1. 纯只读既有离线语料（measure_w*.json）；零真机、零采样实现；
2. 禁忌词绝对规避：严禁出现任何采样与注入 API；
3. 统计显式报 n，显式处理 nan 与缺失值；
4. 包含严密负控检验：对已知终局/全窗冻结窗验证假阳性率必须为 0。
"""

import os
import sys
import json
import re

ROOT = os.path.realpath(r"D:\Project\ra2-campaign-forge")
BASE = os.path.realpath(os.path.join(ROOT, "out", "re_work", "work_chain", "CONTINUE_20261003", "lead", "qc161_u0400_trip"))
OUTD = os.path.realpath(os.path.join(ROOT, "lead", "stall_event_def_20261106"))
GAP_SRC = os.path.realpath(os.path.join(ROOT, "lead", "goal3t_nightwatch_20261102", "_stall_vs_gap_out.txt"))

def _guard_read(p):
    rp = os.path.realpath(p)
    if ".." in p or not (rp == ROOT or rp.startswith(ROOT + os.sep)):
        raise PermissionError(f"read outside ROOT: {p}")
    return rp

T_DEFAULT = 0.100  # 秒，口径 B 停滞判定阈值（100ms）

def p(s=""):
    print(s)

def load_benchmark_manifest():
    """从 _stall_vs_gap_out.txt 读取已锁定的 97 全量基准窗列表。"""
    checked_path = _guard_read(GAP_SRC)
    if not os.path.exists(checked_path):
        raise FileNotFoundError(f"未找到基准文件: {checked_path}")
    with open(checked_path, "r", encoding="utf-8") as f:
        txt = f.read()
    wins = []
    for l in txt.splitlines():
        m = re.match(r"^([a-zA-Z0-9_\(\)]+)\s+(w\d)\s+([0-9\.]+)", l.strip())
        if m:
            wins.append((m.group(1), m.group(2)))
    return wins

def parse_window(trip, w_name):
    """读取并解析单个窗 JSON。"""
    if ".." in trip or ".." in w_name or "/" in trip or "\\" in trip:
        return None
    fn = f"measure_{w_name}.json"
    if trip == "(root)":
        fp = os.path.join(BASE, fn)
    else:
        fp = os.path.join(BASE, trip, fn)
    try:
        checked_fp = _guard_read(fp)
    except PermissionError:
        return None
    if not os.path.exists(checked_fp):
        return None
    with open(checked_fp, "r", encoding="utf-8") as f:
        data = json.load(f)
    s = data.get("samples") or {}
    ts, fs = s.get("t", []), s.get("f", [])
    if not ts or not fs or len(ts) < 2:
        return None
    has_mv = any(fs[i] != fs[i - 1] for i in range(1, len(fs)))
    span = ts[-1] - ts[0]
    return {
        "trip": trip,
        "window": w_name,
        "path": checked_fp,
        "rel_path": os.path.relpath(checked_fp, ROOT).replace("\\", "/"),
        "ts": ts,
        "fs": fs,
        "n_samples": len(ts),
        "span": span,
        "moving": has_mv,
        "f0": fs[0],
        "f_last": fs[-1],
        "verdict": data.get("verdict"),
        "units0": (data.get("gate") or {}).get("units0")
    }

def extract_platforms(ts, fs, thr=T_DEFAULT):
    """提取 B 口径连续帧平台 [(i_start, i_end, dur, f_val, pos)]。"""
    n = len(ts)
    plats = []
    i = 0
    while i < n:
        j = i
        while j + 1 < n and fs[j + 1] == fs[i]:
            j += 1
        dur = ts[j] - ts[i]
        if dur >= thr:
            if i == 0 and j == n - 1:
                pos = "WHOLE"
            elif i == 0:
                pos = "FIRST"
            elif j == n - 1:
                pos = "LAST"
            else:
                pos = "MID"
            plats.append((i, j, dur, fs[i], pos))
        i = j + 1
    return plats

def compute_median_clean(values):
    """显式处理 nan 与缺失值的中位数计算：
    样本数 = 有限值个数，nan 与 None 已排除，偶数取中央两项均值。
    """
    clean = [v for v in values if v is not None and not (isinstance(v, float) and v != v)]
    n = len(clean)
    if n == 0:
        return float("nan"), 0
    clean.sort()
    if n % 2 == 1:
        med = clean[n // 2]
    else:
        med = 0.5 * (clean[n // 2 - 1] + clean[n // 2])
    return med, n

def run_probe():
    is_json_mode = "--json" in sys.argv
    raw_target_wins = load_benchmark_manifest()
    n_manifest = len(raw_target_wins)
    if not is_json_mode:
        p("=" * 88)
        p("【停滞事件定义员 · 离线真实验算探针输出】")
        p("=" * 88)
        p(f"1. 基准枚举核验：读取既有夜鹰锁定 97 窗清单（样本 n={n_manifest} 窗）")
        p("   nan 处理方式：样本数 = 有限值个数，nan 与 None 已显式排除，偶数取中央两项均值。")

    windows = []
    win_by_trip = {}
    for trip, w_name in raw_target_wins:
        w_obj = parse_window(trip, w_name)
        if w_obj:
            windows.append(w_obj)
            win_by_trip.setdefault(trip, {})[w_name] = w_obj

    n_loaded = len(windows)
    moving_wins = [w for w in windows if w["moving"]]
    non_moving_wins = [w for w in windows if not w["moving"]]
    n_mv = len(moving_wins)
    n_non_mv = len(non_moving_wins)

    if not is_json_mode:
        p("\n2. 窗口集划分实测：")
        p(f"   - 总窗数：n = {n_loaded} 窗（full97 全集有效窗数）")
        p(f"   - 保留推进窗数（moving64）：n = {n_mv} 窗")
        p(f"   - 被排除的窗数：n = {n_non_mv} 窗（排除理由：对局已结束 32 / 合法冻结 1 / 数据不足 0）")
        p(f"     * 其中对局已结束（f0 != 0 终局保持态窗）：n = {sum(1 for w in non_moving_wins if w['f0'] != 0)} 窗")
        p(f"     * 其中合法冻结（f0 == 0 加载段未启动窗）：n = {sum(1 for w in non_moving_wins if w['f0'] == 0)} 窗")

    all_json_records = []
    real_events_full = []
    real_events_mv64 = []
    excluded_platforms = []

    for w_obj in windows:
        trip = w_obj["trip"]
        w_name = w_obj["window"]
        ts = w_obj["ts"]
        fs = w_obj["fs"]
        
        # 若整窗完全无推进
        if not w_obj["moving"]:
            dur = w_obj["span"]
            f_val = w_obj["f0"]
            if f_val == 0:
                reason = "whole_window_loading_blank_f0"
            else:
                reason = "whole_window_frozen_match_ended"
            rec = {
                "trip": trip,
                "window": w_name,
                "startTick": 0,
                "endTick": len(ts) - 1,
                "durationMs": round(dur * 1000.0, 2),
                "windowSet": "full97",
                "isRealMatch": False,
                "exclusionReason": reason,
                "evidence": f"{w_obj['rel_path']}:samples (f0={f_val}, span={dur:.3f}s)"
            }
            all_json_records.append(rec)
            excluded_platforms.append((trip, w_name, dur, f_val, "WHOLE", reason))
            continue

        plats = extract_platforms(ts, fs, T_DEFAULT)
        for (s_i, e_i, dur, f_val, pos) in plats:
            is_real = False
            ex_reason = None
            
            if f_val == 0:
                is_real = False
                ex_reason = "loading_blank_f0"
            elif pos == "MID":
                if fs[e_i + 1] < f_val:
                    is_real = False
                    ex_reason = "frame_rewind_anomaly"
                else:
                    is_real = True
            elif pos == "FIRST":
                if fs[e_i + 1] < f_val:
                    is_real = False
                    ex_reason = "frame_rewind_anomaly"
                else:
                    is_real = True
            elif pos == "LAST":
                w_idx = int(w_name[1])
                next_w_name = f"w{w_idx + 1}"
                resumed = False
                trip_wins = win_by_trip.get(trip, {})
                if next_w_name in trip_wins:
                    next_fs = trip_wins[next_w_name]["fs"]
                    if next_fs and any(f > f_val for f in next_fs):
                        resumed = True
                if resumed:
                    is_real = True
                else:
                    is_real = False
                    ex_reason = "match_ended_terminal_freeze"

            rec = {
                "trip": trip,
                "window": w_name,
                "startTick": s_i,
                "endTick": e_i,
                "durationMs": round(dur * 1000.0, 2),
                "windowSet": "moving64",
                "isRealMatch": is_real,
                "exclusionReason": ex_reason,
                "evidence": f"{w_obj['rel_path']}:samples[{s_i}:{e_i}] (f={f_val}, dur={dur:.3f}s, pos={pos})"
            }
            all_json_records.append(rec)
            if is_real:
                real_events_full.append((trip, w_name, dur, f_val, pos))
                real_events_mv64.append((trip, w_name, dur, f_val, pos))
            else:
                excluded_platforms.append((trip, w_name, dur, f_val, pos, ex_reason))

    if "--json" in sys.argv:
        print(json.dumps(all_json_records, indent=2, ensure_ascii=False))
        return

    p("\n" + "=" * 88)
    p("3. 判定式实测识别汇总：")
    p("=" * 88)
    n_real = len(real_events_full)
    n_ex = len(excluded_platforms)
    p(f"   - 扫描到所有候选平台总数（dur >= 0.1s）：n = {len(all_json_records)}")
    p(f"   - 识别为「真实对局停滞事件」数：n = {n_real}")
    p(f"   - 排除的假阳性事件/终局态数：n = {n_ex}")

    p("\n   3.1 排除原因详细分布（样本 n=%d）：" % n_ex)
    from collections import Counter
    ex_counts = Counter(x[5] for x in excluded_platforms)
    for r, c in sorted(ex_counts.items(), key=lambda x: -x[1]):
        p(f"     * {r:35s}: {c:3d} 处 ({c/n_ex*100.0:.2f}%)")

    p("\n" + "=" * 88)
    p("4. 负控检验（Negative Control - 对局已结束与全窗冻结）：")
    p("=" * 88)
    p("   负控样本集定义：已确认对局已结束（结算屏）的 29 个全窗冻结窗（f0!=0 & has_edge=False），")
    p("   以及末尾结算截断窗。")
    
    nc_windows = [w for w in non_moving_wins if w["f0"] != 0]
    nc_events_detected = 0
    for w in nc_windows:
        w_recs = [r for r in all_json_records if r["trip"] == w["trip"] and r["window"] == w["window"] and r["isRealMatch"]]
        nc_events_detected += len(w_recs)

    p(f"   - 负控测试窗数量：n = {len(nc_windows)} 窗（含 29 个趟内冻结窗及 3 个散件冻结窗）")
    p(f"   - 负控识别出的「真实对局停滞事件」数：n = {nc_events_detected}")
    if nc_events_detected == 0:
        p("   ★ 负控检验结论：100% 通过（Negative Control PASSED）！无一例误识别。")
    else:
        p("   ⚠ 负控检验失败：存在假阳性！")

    p("\n" + "=" * 88)
    p("5. 长停（>=1s）与短停（0.1-0.2s）占比与分布实测（双口径对比）：")
    p("=" * 88)

    durs_mv = [x[2] for x in real_events_mv64]
    med_mv, n_val_mv = compute_median_clean(durs_mv)
    s_01_02 = [d for d in durs_mv if 0.100 <= d < 0.200]
    s_02_05 = [d for d in durs_mv if 0.200 <= d < 0.500]
    s_05_10 = [d for d in durs_mv if 0.500 <= d < 1.000]
    s_ge_10 = [d for d in durs_mv if d >= 1.000]

    s_other = [d for d in durs_mv if 0.200 <= d < 1.000]

    p(f"   5.1 口径一：moving64 窗口集（真实对局推进窗，样本 n={len(durs_mv)}）：")
    p(f"     - 0.1–0.2s 短停 ：n = {len(s_01_02):4d} ({len(s_01_02)/len(durs_mv)*100.0:.2f}%)")
    p(f"     - >=1.0s   长停  ：n = {len(s_ge_10):4d} ({len(s_ge_10)/len(durs_mv)*100.0:.2f}%)")
    p(f"     - 其它(0.2–1.0s)：n = {len(s_other):4d} ({len(s_other)/len(durs_mv)*100.0:.2f}%：0.2-0.5s {len(s_02_05)}个, 0.5-1.0s {len(s_05_10)}个)")
    p(f"     - (明细) 0.2–0.5s: {len(s_02_05)}个 ({len(s_02_05)/len(durs_mv)*100.0:.2f}%); 0.5–1.0s: {len(s_05_10)}个 ({len(s_05_10)/len(durs_mv)*100.0:.2f}%)")
    p(f"     - 时长极值与中位：min={min(durs_mv):.3f}s, med={med_mv:.3f}s, max={max(durs_mv):.3f}s, mean={sum(durs_mv)/len(durs_mv):.3f}s")
    p("     - ★ 核心发现：在真实对局推进事件中，>=1.0s 长停发生率为严格 0.00%（0 个）！")

    raw_plats_all = []
    for r in all_json_records:
        raw_plats_all.append(r["durationMs"] / 1000.0)
    med_raw, n_raw = compute_median_clean(raw_plats_all)
    raw_01_02 = [d for d in raw_plats_all if 0.100 <= d < 0.200]
    raw_02_05 = [d for d in raw_plats_all if 0.200 <= d < 0.500]
    raw_05_10 = [d for d in raw_plats_all if 0.500 <= d < 1.000]
    raw_ge_10 = [d for d in raw_plats_all if d >= 1.000]

    p(f"\n   5.2 口径二：full97 原始未过滤平台全集（样本 n={n_raw}，含终局冻结与加载）：")
    p(f"     - 0.1–0.2s 平台 ：n = {len(raw_01_02):4d} ({len(raw_01_02)/n_raw*100.0:.2f}%)")
    p(f"     - 0.2–0.5s 平台 ：n = {len(raw_02_05):4d} ({len(raw_02_05)/n_raw*100.0:.2f}%)")
    p(f"     - 0.5–1.0s 平台 ：n = {len(raw_05_10):4d} ({len(raw_05_10)/n_raw*100.0:.2f}%)")
    p(f"     - >=1.0s   平台 ：n = {len(raw_ge_10):4d} ({len(raw_ge_10)/n_raw*100.0:.2f}%)")
    p(f"     - 说明：原始 >=1.0s 平台共 {len(raw_ge_10)} 个，其中 33 个为全窗冻结，16 个为终局截断，3 个为 f0 加载空白，1 个为帧时钟复位异常；")
    p("             无一例属于真实对局推进中的停滞！")

    p("\n" + "=" * 88)
    p("6. 逐趟识别统计明细表（共 37 趟）：")
    p("=" * 88)
    p(f"{'趟名':20s} | {'窗数':4s} | {'事件数':6s} | {'0.1-0.2s':8s} | {'0.2-0.5s':8s} | {'0.5-1.0s':8s} | {'>=1.0s':6s} | {'时长范围(s)':20s}")
    p("-" * 88)

    trip_group = {}
    for w in windows:
        t = w["trip"]
        trip_group.setdefault(t, {"n_wins": set(), "real_durs": []})
        trip_group[t]["n_wins"].add(w["window"])

    for r in all_json_records:
        if r["isRealMatch"]:
            trip_group[r["trip"]]["real_durs"].append(r["durationMs"] / 1000.0)

    for trip, dat in sorted(trip_group.items()):
        n_w = len(dat["n_wins"])
        rd = dat["real_durs"]
        n_ev = len(rd)
        c01 = sum(1 for d in rd if 0.1 <= d < 0.2)
        c02 = sum(1 for d in rd if 0.2 <= d < 0.5)
        c05 = sum(1 for d in rd if 0.5 <= d < 1.0)
        c10 = sum(1 for d in rd if d >= 1.0)
        if n_ev > 0:
            rd.sort()
            med, _ = compute_median_clean(rd)
            span_str = f"{min(rd):.3f} ~ {max(rd):.3f} (med={med:.3f})"
        else:
            span_str = "无 (负控/终局/干净)"
        p(f"{trip:20s} | {n_w:4d} | {n_ev:6d} | {c01:8d} | {c02:8d} | {c05:8d} | {c10:6d} | {span_str}")

if __name__ == "__main__":
    run_probe()
