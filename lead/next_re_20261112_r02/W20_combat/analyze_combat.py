#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""NEXT_RE_20261112_R02 / W20 —— RE-N04i 战斗维度离线重算（零输入 600 s）。

输入：W20_combat/out/run.ndjson + ui_watch.ndjson + meta.json + skirmish_settings.json
输出：W20_combat/out/analysis.json + W20_combat/out/tickcost.csv + stdout 摘要

★ 主判读通道 = cycle（QueryThreadCycleTime）；FILETIME 仅交叉核对（记账量子
  15.625 ms，中位 0 是量子产物，不得读作"拍快"）。
★ cycle→ms 标定（本趟全段自标定，不硬编码 cyc/ms 常数）：
  cyc_per_ms = Σ(逐拍 cycle Δ) / Σ(逐拍 FILETIME Δ CPU ms)（量子抵消）。
  口径勘误（如实记录）：W15 卡面 3.104e9 实为 cyc/s（≈3.104 GHz 时钟频率）；
  正确 cyc/ms 口径 = 3.104e6。臂间各用各自全段自标定。
★ 预设判据（卡面固定，不得事后改）：
  [观测到战斗信号] = 0xA8ED50 出现非零（旁证，语义未证，不当 Bullet 实数）；
  [CPU 显著抬升]   = 每拍 CPU 中位 > 2.54 ms（=A 1.691×1.5）或占用率 > 10%（基线 5.39%）；
  [中间地带]       = 相对 A 中位 +20%–+50%；
  [无显著差异]     = 相对 A 中位 <20% 且 0xA8ED50 全程 0；
  [数据不足]       = 有效局内段 <300 s（不重启补测）。
★ 四臂对照（本卡必交付）：A（W15，52 建筑，1.691 ms / 5.39%）/ HexBay（W18，144 建筑，
  1.767 ms / 5.67%）/ U800（W19，480 车+320 步兵，1.336 ms / 4.26%）/ 本卡（战斗维度）。
★ 战斗检验：0xA8ED50 首次非零时刻 前 60 s vs 后 60 s 每拍 CPU 中位对照——
  "战斗是否更贵"的直接检验；窗长不足 60 s 时用可用窗并如实标注。
★ 0xA8ED50 语义未证：只作"是否可能开战"旁证；「没观测到 ≠ 不存在」。
★ 逐拍 CPU 均值/占用率必须与「一拍 CPU 低 ≠ 拍快」同读（CPU 不含阻塞等待）。
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from pathlib import Path

W20 = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W20_combat")
OUT = W20 / "out"
NS_MS = 1e6

# A 臂基线（W15 实测；开工前固定）
A_BASE = {
    "carrier": "[8]试验地_Pro_ProvingGrounds.yrm ([8] Proving Grounds, 52 建筑)",
    "cycle_median_ms_per_tick": 1.691,
    "filetime_mean_ms_per_tick": 1.725,
    "occupancy_pct_singlecore": 5.39,
    "tick_rate_counts_per_s": 31.2492,
    "tick_interval_mean_ms": 32.000,
    "tick_interval_ge64ms": 0,
    "cyc_per_ms_w15_card": 3.104e9,        # 卡面原值（实为 cyc/s，≈3.104 GHz 时钟频率）
    "cyc_per_ms_w15_corrected": 3.104e6,   # 口径修正：cyc/s → cyc/ms（卡面单位勘误）
    "ingame_s": 240.006,
    "a8ed50": "全程 0（W7/W15/W18/W19 四卡一致）",
}
# HexBay 臂锚点（W18 analysis.json 实读；并列对照）
HEXBAY_BASE = {
    "carrier": "[8]黑心湾_HexBay.yrm (Hex Bay (2-8), 144 建筑)",
    "cycle_median_ms_per_tick": 1.767189,
    "occupancy_pct_singlecore": 5.670446,
    "cyc_per_ms_selfcalibrated": 3311138.27,
    "whole_segment_cps": 31.249279,
    "tick_interval_ge64ms": 0,
    "rel_change_vs_a_median_pct": 4.506,
    "a8ed50_all_zero": True,
    "ingame_s": 240.005534,
    "tier": "[无显著差异]",
}
# U800 臂锚点（W19 analysis.json 实读；并列对照）
U800_BASE = {
    "carrier": "[2]0LoadBench_U0800.yrm ([2] 0LoadBench U800, 480 车+320 步兵)",
    "cycle_median_ms_per_tick": 1.335814,
    "occupancy_pct_singlecore": 4.264229,
    "cyc_per_ms_selfcalibrated": 3247646.89,
    "whole_segment_cps": 31.249227,
    "tick_interval_ge64ms": 0,
    "rel_change_vs_a_median_pct": -21.0,
    "a8ed50_all_zero": True,
    "ingame_s": 240.006,
    "tier": "[中间地带]",
}
VERDICT_THRESH_MS = 2.54       # A 中位 × 1.5
VERDICT_THRESH_OCC = 10.0      # 单核 %
VERDICT_SEG_MIN_S = 300.0      # [数据不足] 阈值
MID_LO = 0.20
MID_HI = 0.50


def load_ndjson(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                rows.append({"kind": "_unparsable"})
    return rows


def pct(sorted_vals, p):
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / math.sqrt(sxx * syy)


def spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    return pearson(ranks(xs), ranks(ys))


def histogram(vals, bin_ms=1.0, max_bins=64):
    if not vals:
        return {}
    bins = {}
    for v in vals:
        b = min(int(v / bin_ms), max_bins - 1) * bin_ms
        bins[b] = bins.get(b, 0) + 1
    return {("%g-%g" % (b, b + bin_ms)): bins[b] for b in sorted(bins.keys())}


def dist_stats(vals):
    s = sorted(vals)
    return {
        "n": len(s),
        "min_ms": s[0] if s else None,
        "median_ms": pct(s, 50),
        "p90_ms": pct(s, 90),
        "p99_ms": pct(s, 99),
        "max_ms": s[-1] if s else None,
        "mean_ms": (sum(s) / len(s)) if s else None,
    }


def main():
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None, help="覆盖 out 目录（自测用）")
    a = ap.parse_args()
    if a.dir:
        OUT = Path(a.dir)
    samples = [r for r in load_ndjson(OUT / "run.ndjson")
               if r.get("kind") == "sample"]
    events = [r for r in load_ndjson(OUT / "run.ndjson")
              if r.get("kind") == "event"]
    watcher = load_ndjson(OUT / "ui_watch.ndjson") \
        if (OUT / "ui_watch.ndjson").exists() else []
    meta = json.loads((OUT / "meta.json").read_text(encoding="utf-8"))

    print("samples=%d events=%d watcher=%d" %
          (len(samples), len(events), len(watcher)))
    print("meta: pid=%s map=%s idx=%s phase_stop=%s err=%s" %
          (meta.get("pid"), (meta.get("map") or {}).get("display_name"),
           (meta.get("map") or {}).get("index"),
           meta.get("phase_stop"), meta.get("error")))
    print("carrier: %s B (expected %s) sha_ok=%s" %
          ((meta.get("carrier") or {}).get("bytes"),
           (meta.get("carrier") or {}).get("expected_bytes"),
           (meta.get("carrier") or {}).get("sha256")
           == (meta.get("carrier") or {}).get("expected_sha256")))

    # ---------- 有效局内段 ----------
    seg = [s for s in samples if s.get("phase") == "ingame"
           and s.get("read_status") == "ok"]
    post = [s for s in samples if s.get("phase") == "post_end"]
    if not seg:
        print("!! 无 ingame ok 采样 ⇒ 未进图 ⇒ [数据不足]")
        verdict = "[数据不足]"
        _dump_min(OUT, verdict, {"reason": "no_ingame_samples",
                                 "phase_stop": meta.get("phase_stop"),
                                 "error": meta.get("error")})
        return 1
    t0 = seg[0]["t_mono_ns"]
    t1 = seg[-1]["t_mono_ns"]
    seg_wall_s = (t1 - t0) / 1e9
    for s in seg:
        s["_t_rel_s"] = (s["t_mono_ns"] - t0) / 1e9

    # 采样间隔实测
    ints = [s["interval_ms_actual"] for s in seg
            if s.get("interval_ms_actual") is not None]
    samp_int = dist_stats(ints)
    samp_int["over20_ms"] = sum(1 for v in ints if v > 20.0)
    print("sampling interval: n=%d median=%.3f p90=%.3f p99=%.3f max=%.3f >20ms=%d" %
          (samp_int["n"], samp_int["median_ms"], samp_int["p90_ms"],
           samp_int["p99_ms"], samp_int["max_ms"], samp_int["over20_ms"]))

    # ---------- 递增事件与 CPU 归属（与 W15/W19 完全同规则） ----------
    hiccup_thresh = max(3.0 * (samp_int["median_ms"] or 6.0), 24.0)
    all_by_seq = {s["seq"]: s for s in samples}
    rows = []
    prev_ev = None
    seen_first_ingame = False
    for s in samples:
        if s.get("phase") == "post_end":
            break
        ok = (s.get("read_status") == "ok" and s.get("win_cpu_ms") is not None
              and not s.get("win_thread_err"))
        if s.get("phase") == "ingame":
            seen_first_ingame = True
        if not seen_first_ingame:
            if ok:
                prev_ev = s
            continue
        f = s.get("frame")
        if ok and f is not None:
            if prev_ev is None:
                prev_ev = s
                continue
            pf = prev_ev.get("frame")
            if f > pf:
                seq_lo, seq_hi = prev_ev["seq"], s["seq"]
                gap, hiccup, worst = False, False, None
                for q in range(seq_lo + 1, seq_hi + 1):
                    qq = all_by_seq.get(q)
                    if qq is None:
                        continue
                    if qq.get("read_status") != "ok" \
                            or qq.get("win_cpu_ms") is None \
                            or qq.get("win_thread_err"):
                        gap = True
                    if qq.get("interval_ms_actual") is not None:
                        if qq["interval_ms_actual"] > hiccup_thresh:
                            hiccup = True
                        if worst is None or qq["interval_ms_actual"] > worst:
                            worst = qq["interval_ms_actual"]
                cyc = None
                if (s.get("win_cycle") is not None
                        and prev_ev.get("win_cycle") is not None):
                    cyc = s["win_cycle"] - prev_ev["win_cycle"]
                rows.append({
                    "idx": len(rows) + 1,
                    "t_rel_s": (s["t_mono_ns"] - t0) / 1e9,
                    "interval_ms": (s["t_mono_ns"] - prev_ev["t_mono_ns"]) / NS_MS,
                    "cpu_ms": s["win_cpu_ms"] - prev_ev["win_cpu_ms"],
                    "frame": f, "mode": s.get("mode_A8B238"),
                    "fg": s.get("win_foreground"), "df": f - pf,
                    "gap": gap, "hiccup": hiccup, "worst_bracket_ms": worst,
                    "win_cyc_delta": cyc,
                    "win_cpu_cum_ms": s["win_cpu_ms"],
                    "win_kernel_cum_ms": s.get("win_kernel_ms"),
                    "win_user_cum_ms": s.get("win_user_ms"),
                    "ctx": s.get("ctx") if s.get("ctx") is not None
                           else s.get("win_ctx_switches"),
                    "A8ED50": s.get("A8ED50"), "B0CE88": s.get("B0CE88"),
                    "87E8E0": s.get("87E8E0"),
                    "_seq": seq_hi,
                })
                prev_ev = s
            elif f < pf:
                rows.append({"idx": len(rows) + 1,
                             "t_rel_s": (s["t_mono_ns"] - t0) / 1e9,
                             "interval_ms": None, "cpu_ms": None, "frame": f,
                             "mode": s.get("mode_A8B238"),
                             "fg": s.get("win_foreground"), "df": None,
                             "gap": True, "note": "frame_regression"})
                prev_ev = s
    ok_rows = [r for r in rows if r.get("cpu_ms") is not None and not r["gap"]]
    d1 = [r for r in ok_rows if r.get("df") == 1]
    dmulti = [r for r in ok_rows if (r.get("df") or 0) >= 2]
    gap_rows = [r for r in rows if r["gap"] and r.get("cpu_ms") is None]
    print("events: total=%d ok=%d df1=%d df2+=%d gap=%d" %
          (len(rows), len(ok_rows), len(d1), len(dmulti), len(gap_rows)))

    # ---------- cycle 标定（全段长窗，量子抵消） ----------
    cyc_rows = [r for r in d1 if r.get("win_cyc_delta")]
    tot_cyc = sum(r["win_cyc_delta"] for r in cyc_rows)
    tot_cpu = sum(r["cpu_ms"] for r in cyc_rows)
    cyc_per_ms_b = (tot_cyc / tot_cpu) if tot_cpu > 0 else None
    print("cycle calibration: tot_cyc=%.4g tot_cpu=%.3fms cyc_per_ms_W20=%.4g "
          "(A/W15 corrected=3.104e6 [卡面 3.104e9 为 cyc/s，勘误]; W18=3.311e6; "
          "W19=3.248e6; ratio=%.4f)" %
          (tot_cyc, tot_cpu, cyc_per_ms_b or -1,
           (cyc_per_ms_b / A_BASE["cyc_per_ms_w15_corrected"]) if cyc_per_ms_b else -1))

    # ---------- 每拍 CPU：cycle 主判读 + FILETIME 交叉核对 ----------
    for r in d1:
        r["cyc_ms"] = (r["win_cyc_delta"] / cyc_per_ms_b
                       if (cyc_per_ms_b and r.get("win_cyc_delta") is not None)
                       else None)
        r["cyc_ms_A_factor"] = (r["win_cyc_delta"] / A_BASE["cyc_per_ms_w15_corrected"]
                                if r.get("win_cyc_delta") is not None else None)
    cyc_vals = sorted(r["cyc_ms"] for r in d1 if r["cyc_ms"] is not None)
    ft_vals = sorted(r["cpu_ms"] for r in d1)
    cyc_dist = dist_stats(cyc_vals)
    ft_dist = dist_stats(ft_vals)
    print("[cycle 主判读] per-tick CPU: n=%d min=%.3f med=%.3f p90=%.3f p99=%.3f "
          "max=%.3f mean=%.3f (ms)" %
          (cyc_dist["n"], cyc_dist["min_ms"], cyc_dist["median_ms"],
           cyc_dist["p90_ms"], cyc_dist["p99_ms"], cyc_dist["max_ms"],
           cyc_dist["mean_ms"]))
    print("[FILETIME 交叉] per-tick CPU: n=%d min=%.3f med=%.3f p90=%.3f p99=%.3f "
          "max=%.3f mean=%.3f (ms)" %
          (ft_dist["n"], ft_dist["min_ms"],
           ft_dist["median_ms"], ft_dist["p90_ms"], ft_dist["p99_ms"],
           ft_dist["max_ms"], ft_dist["mean_ms"]))
    hist1 = histogram(cyc_vals, 1.0)
    print("cycle histogram (1ms bins):", {k: v for k, v in hist1.items()})

    # ---------- 进图判定：帧率（预设 ≈29–32 计数/s 持续 ≥60 s） ----------
    w_by_10s = {}
    for r in d1:
        w = int(r["t_rel_s"] // 10)
        w_by_10s.setdefault(w, []).append(r)
    win_cps = []
    for w, rs in w_by_10s.items():
        df_sum = sum(r["df"] for r in rs)
        wall = max(r["t_rel_s"] for r in rs) - min(
            r["t_rel_s"] for r in rs)
        wall += (rs[0]["interval_ms"] or 0) / 1000.0
        cps = df_sum / wall if wall > 0 else None
        win_cps.append({"w": w, "cps": cps, "n_ticks": len(rs)})
    cps_list = [w["cps"] for w in win_cps if w["cps"]]
    cps_med = pct(sorted(cps_list), 50) if cps_list else None
    cps_min = min(cps_list) if cps_list else None
    cps_max = max(cps_list) if cps_list else None
    entered = bool(seg_wall_s >= 60.0 and cps_med and cps_med >= 29.0
                   and cps_max and cps_max <= 33.0
                   and (cps_min is None or cps_min >= 25.0))
    print("map-entry check: wall=%.3fs cps per 10s win median=%.3f min=%.3f "
          "max=%.3f -> entered=%s" %
          (seg_wall_s, cps_med or -1, cps_min or -1, cps_max or -1, entered))
    print("  cps windows:", ["w%d=%.2f" % (w["w"], w["cps"])
                              for w in win_cps if w["cps"]])
    tot_df = sum(r["df"] for r in d1)
    cps_whole = tot_df / seg_wall_s if seg_wall_s > 0 else None
    print("  whole-segment tick rate = %.4f counts/s (A: 31.2492)" % (cps_whole or -1))

    # ---------- 占用率（单核 %）：cycle 与 FILETIME 双口径 ----------
    win_cum = [s["win_cpu_ms"] for s in seg if s.get("win_cpu_ms") is not None]
    occ_ft = ((win_cum[-1] - win_cum[0]) / 1000.0 / seg_wall_s * 100.0
              if len(win_cum) >= 2 else None)
    first_c = None
    last_c = None
    for s in seg:
        if s.get("win_cycle") is not None:
            if first_c is None:
                first_c = s["win_cycle"]
            last_c = s["win_cycle"]
    occ_cyc = ((last_c - first_c) / cyc_per_ms_b / 1000.0 / seg_wall_s * 100.0
               if (first_c is not None and last_c is not None and cyc_per_ms_b)
               else None)
    print("occupancy: window-thread cycle=%.2f%% filetime=%.2f%% (single-core; "
          "A: 5.39%%)" % (occ_cyc or -1, occ_ft or -1))

    # ---------- ★ 0xA8ED50 时间线（Q1 主判据） ----------
    a8_ingame = [r.get("A8ED50") for r in ok_rows if r.get("A8ED50") is not None]
    n_a8 = len(a8_ingame)
    n_a8_nz = sum(1 for v in a8_ingame if v != 0)
    first_nz_ingame = None
    for r in ok_rows:
        v = r.get("A8ED50")
        if v is not None and v != 0:
            first_nz_ingame = {"t_rel_s": r["t_rel_s"], "value": v,
                               "frame": r["frame"]}
            break
    # 非零持续段（相邻非零拍合并，>2s 间隔断开）
    streaks = []
    cur = None
    for r in ok_rows:
        v = r.get("A8ED50")
        nz = v is not None and v != 0
        if nz:
            if cur is not None and r["t_rel_s"] - cur["t_end_s"] <= 2.0:
                cur["t_end_s"] = r["t_rel_s"]
                cur["n_ticks"] += 1
                cur["max"] = max(cur["max"], v)
            else:
                cur = {"t_start_s": r["t_rel_s"], "t_end_s": r["t_rel_s"],
                       "n_ticks": 1, "max": v}
                streaks.append(cur)
        else:
            cur = None
    a8_timeline = {
        "n_ticks_df1_ok": n_a8,
        "n_nonzero": n_a8_nz,
        "nonzero_ratio": (n_a8_nz / n_a8) if n_a8 else None,
        "first_nonzero_ingame": first_nz_ingame,
        "value_min": min(a8_ingame) if a8_ingame else None,
        "value_max": max(a8_ingame) if a8_ingame else None,
        "n_distinct_values": len(set(a8_ingame)) if a8_ingame else 0,
        "nonzero_streaks_top10": sorted(
            streaks, key=lambda x: -x["n_ticks"])[:10],
        "nonzero_streak_count": len(streaks),
        "semantics_note": "0xA8ED50 候选 BulletCnt 语义未证；只作开战旁证，"
                          "不得当已证 Bullet 数；「没观测到 ≠ 不存在」",
    }
    print("A8ED50 timeline: n=%d nonzero=%d ratio=%.4f first=%s streaks=%d "
          "vmin=%s vmax=%s distinct=%s" %
          (n_a8, n_a8_nz, a8_timeline["nonzero_ratio"] or 0.0,
           first_nz_ingame, len(streaks),
           a8_timeline["value_min"], a8_timeline["value_max"],
           a8_timeline["n_distinct_values"]))
    ev_bullet = [e for e in events if e.get("event") == "a8ed50_first_nonzero"]
    print("probe events a8ed50_first_nonzero: %s" %
          (ev_bullet[0].get("detail") if ev_bullet else "none"))

    # ---------- ★ 60 s 分段 CPU（cycle 通道） ----------
    seg60 = []
    n60 = max(int(math.ceil(seg_wall_s / 60.0)), 1)
    for k in range(n60):
        lo, hi = k * 60.0, min((k + 1) * 60.0, seg_wall_s)
        rs = [r for r in d1 if lo <= r["t_rel_s"] < hi and r["cyc_ms"] is not None]
        vals = sorted(r["cyc_ms"] for r in rs)
        nz = sum(1 for r in rs if (r.get("A8ED50") or 0) != 0)
        seg60.append({"seg": k, "t_lo_s": lo, "t_hi_s": hi, "n": len(vals),
                      "median_ms": pct(vals, 50), "max_ms": vals[-1] if vals else None,
                      "a8ed50_nonzero_ticks": nz,
                      "a8ed50_nonzero_ratio": (nz / len(rs)) if rs else None})
    for s6 in seg60:
        print("seg60 %02d [%6.1f-%6.1fs] n=%5d med=%.3fms max=%.3fms "
              "a8_nz=%d (%.2f%%)" %
              (s6["seg"], s6["t_lo_s"], s6["t_hi_s"], s6["n"],
               s6["median_ms"] or -1, s6["max_ms"] or -1,
               s6["a8ed50_nonzero_ticks"],
               (s6["a8ed50_nonzero_ratio"] or 0.0) * 100.0))
    med_seg0 = seg60[0]["median_ms"] if seg60 else None
    seg_medians = [s["median_ms"] for s in seg60 if s["median_ms"] is not None]
    rising_segs = []
    if med_seg0:
        for s6 in seg60:
            if s6["median_ms"] is not None and s6["median_ms"] > med_seg0 * 1.2:
                rising_segs.append({"seg": s6["seg"],
                                    "ratio_vs_seg0": s6["median_ms"] / med_seg0})
    print("seg60 rising candidates (>+20%% vs seg0 med=%.3f): %s" %
          (med_seg0 or -1, rising_segs or "无"))

    # ---------- ★ 战斗前后 60 s CPU 对照（Q2 直接检验） ----------
    combat_contrast = None
    if first_nz_ingame is not None:
        tstar = first_nz_ingame["t_rel_s"]
        pre_rs = [r for r in d1 if r["cyc_ms"] is not None
                  and tstar - 60.0 <= r["t_rel_s"] < tstar]
        post_rs = [r for r in d1 if r["cyc_ms"] is not None
                   and tstar <= r["t_rel_s"] < tstar + 60.0]
        pre_vals = sorted(r["cyc_ms"] for r in pre_rs)
        post_vals = sorted(r["cyc_ms"] for r in post_rs)
        pre_med = pct(pre_vals, 50)
        post_med = pct(post_vals, 50)
        rel = ((post_med - pre_med) / pre_med) if (pre_med and post_med) else None
        combat_contrast = {
            "t_star_s": tstar,
            "window_s": 60.0,
            "pre": {"n": len(pre_vals), "median_ms": pre_med,
                    "mean_ms": (sum(pre_vals) / len(pre_vals)) if pre_vals else None,
                    "actual_window_s": (tstar - pre_rs[0]["t_rel_s"])
                    if pre_rs else 0.0},
            "post": {"n": len(post_vals), "median_ms": post_med,
                     "mean_ms": (sum(post_vals) / len(post_vals)) if post_vals else None,
                     "actual_window_s": (post_rs[-1]["t_rel_s"] - tstar)
                     if post_rs else 0.0},
            "rel_change_pct": (rel * 100.0) if rel is not None else None,
            "note": "窗长不足 60 s 时用可用窗（actual_window_s 如实标注）；"
                    "这是'战斗是否更贵'的直接检验",
        }
        print("combat contrast @t=%.1fs: pre med=%.3fms (n=%d, w=%.1fs) | "
              "post med=%.3fms (n=%d, w=%.1fs) | rel=%+.1f%%" %
              (tstar, pre_med or -1, len(pre_vals),
               combat_contrast["pre"]["actual_window_s"],
               post_med or -1, len(post_vals),
               combat_contrast["post"]["actual_window_s"],
               (rel or 0) * 100.0))
    else:
        print("combat contrast: A8ED50 全程 0 ⇒ 无战斗时刻可对照")

    # ---------- ★ 补充判读 1：A8ED50 非零拍 vs 零拍的条件 CPU（同段内直接对照） ----------
    nz_cpu = sorted(r["cyc_ms"] for r in d1
                    if r["cyc_ms"] is not None and (r.get("A8ED50") or 0) != 0)
    z_cpu = sorted(r["cyc_ms"] for r in d1
                   if r["cyc_ms"] is not None and (r.get("A8ED50") or 0) == 0)
    nz_stats = dist_stats(nz_cpu) if nz_cpu else {"n": 0}
    z_stats = dist_stats(z_cpu) if z_cpu else {"n": 0}
    cond_cpu = {
        "nonzero_ticks": nz_stats,
        "zero_ticks": z_stats,
        "note": "同段内 A8ED50 非零拍 vs 零拍的每拍 CPU 对照（cycle 通道）；"
                "A8ED50 语义未证，只作旁证分桶，不归因",
    }
    if nz_cpu and z_cpu:
        cond_cpu["median_rel_change_pct"] = \
            ((pct(nz_cpu, 50) - pct(z_cpu, 50)) / pct(z_cpu, 50)) * 100.0
    print("cond CPU: nz med=%.3fms (n=%d) | z med=%.3fms (n=%d) | rel=%s" %
          (pct(nz_cpu, 50) if nz_cpu else -1, len(nz_cpu),
           pct(z_cpu, 50) if z_cpu else -1, len(z_cpu),
           ("%.1f%%" % cond_cpu["median_rel_change_pct"])
           if "median_rel_change_pct" in cond_cpu else "n/a"))
    # 按值分桶（0/1/2/3）
    by_val = {}
    for r in d1:
        if r["cyc_ms"] is None:
            continue
        by_val.setdefault(r.get("A8ED50"), []).append(r["cyc_ms"])
    val_table = {str(k): {"n": len(v), "median_ms": pct(sorted(v), 50),
                          "mean_ms": sum(v) / len(v)} for k, v in sorted(by_val.items())}
    print("A8ED50 value buckets:", json.dumps(val_table, ensure_ascii=False))

    # ---------- ★ 补充判读 2：fg True/False 条件 CPU（排除前台丢失干扰） ----------
    fg_t = sorted(r["cyc_ms"] for r in d1
                  if r["cyc_ms"] is not None and r.get("fg"))
    fg_f = sorted(r["cyc_ms"] for r in d1
                  if r["cyc_ms"] is not None and not r.get("fg"))
    fg_effect = {
        "fg_true_ticks": {"n": len(fg_t), "median_ms": pct(fg_t, 50),
                          "mean_ms": (sum(fg_t) / len(fg_t)) if fg_t else None},
        "fg_false_ticks": {"n": len(fg_f), "median_ms": pct(fg_f, 50),
                           "mean_ms": (sum(fg_f) / len(fg_f)) if fg_f else None},
        "note": "本趟存在两段非本意前台丢失（详见 RUNLOG 误干预记录）；"
                "此对照用于判断前台状态是否影响每拍 CPU——帧循环全程 31.25 计数/s。",
    }
    print("fg effect: True med=%.3fms (n=%d) | False med=%.3fms (n=%d)" %
          (pct(fg_t, 50) if fg_t else -1, len(fg_t),
           pct(fg_f, 50) if fg_f else -1, len(fg_f)))
    # fg 状态翻转时间线（粗粒度）
    fg_flips = []
    prev_fg = None
    for r in d1:
        cur_fg = r.get("fg")
        if prev_fg is not None and cur_fg != prev_fg:
            fg_flips.append({"t_rel_s": r["t_rel_s"], "to": bool(cur_fg)})
        prev_fg = cur_fg
    fg_effect["flips_df1"] = fg_flips
    print("fg flips (df1 view):", fg_flips)

    # ---------- ★ 补充判读 3：战斗重窗 vs 安静窗（非零拍占比主 导的分段对照） ----------
    quiet = [r["cyc_ms"] for r in d1 if r["cyc_ms"] is not None
             and r["t_rel_s"] < 240.0]
    heavy = [r["cyc_ms"] for r in d1 if r["cyc_ms"] is not None
             and r["t_rel_s"] >= 480.0]
    heavy_nz = sum(1 for r in d1 if r["cyc_ms"] is not None
                   and r["t_rel_s"] >= 480.0 and (r.get("A8ED50") or 0) != 0)
    window_contrast = {
        "quiet_0_240": {"n": len(quiet), "median_ms": pct(sorted(quiet), 50),
                        "a8ed50_nonzero": 0},
        "heavy_480_600": {"n": len(heavy), "median_ms": pct(sorted(heavy), 50),
                          "a8ed50_nonzero_ticks": heavy_nz,
                          "a8ed50_nonzero_ratio": (heavy_nz / len(heavy))
                          if heavy else None},
        "note": "安静窗=[0,240)s（A8ED50 全零段）；战斗重窗=[480,600)s（非零拍占比"
                "最高的两段合并）；两窗同臂同图同设置，差异只来自时间演化（含战斗）。",
    }
    if quiet and heavy:
        window_contrast["median_rel_change_pct"] = \
            ((pct(sorted(heavy), 50) - pct(sorted(quiet), 50))
             / pct(sorted(quiet), 50)) * 100.0
    print("window contrast: quiet med=%.3fms | heavy med=%.3fms | rel=%s" %
          (pct(sorted(quiet), 50) if quiet else -1,
           pct(sorted(heavy), 50) if heavy else -1,
           ("%.1f%%" % window_contrast["median_rel_change_pct"])
           if "median_rel_change_pct" in window_contrast else "n/a"))

    # ---------- 热点候选（cycle 通道；沿用 W15 判据作旁证参考） ----------
    med_c = cyc_dist["median_ms"] or 0.0
    hot = [r for r in d1 if r["cyc_ms"] is not None
           and r["cyc_ms"] >= 3.0 * med_c and r["cyc_ms"] >= 1.0]
    hot.sort(key=lambda r: -r["cyc_ms"])
    print("cycle hotspots (>=3x med AND >=1.0ms): %d hits" % len(hot))
    for r in hot[:20]:
        print("  t=%7.3fs cyc~%7.3fms frame=%s mode=%s fg=%s int=%.2fms "
              "A8ED50=%s" %
              (r["t_rel_s"], r["cyc_ms"], r["frame"], r["mode"], r["fg"],
               r["interval_ms"] or -1, r.get("A8ED50")))

    # ---------- FILETIME 量子复核 ----------
    nz = []
    prev = None
    for s in seg:
        c = s.get("win_cpu_ms")
        if c is None:
            prev = None
            continue
        if prev is not None:
            dt = (s["t_mono_ns"] - prev[0]) / NS_MS
            d = c - prev[1]
            if 1.0 < dt < 30.0 and d > 1e-9:
                nz.append(round(d, 6))
        prev = (s["t_mono_ns"], c)
    distinct = sorted(set(nz))
    quantum = {"n_nonzero_pairs": len(nz),
               "distinct_nonzero_first12": distinct[:12],
               "min_nonzero_ms": distinct[0] if distinct else None,
               "all_multiple_of_15_625": (all(abs(v / 15.625
                       - round(v / 15.625)) < 0.01 for v in distinct)
                       if distinct else None)}
    print("quantum check: nonzero_pairs=%d distinct[:12]=%s" %
          (quantum["n_nonzero_pairs"], quantum["distinct_nonzero_first12"]))

    # ---------- 10 s 窗趋势（cycle 通道 + 占用率通道） ----------
    trend = []
    for w in sorted(w_by_10s.keys()):
        rs = w_by_10s[w]
        vals = sorted(r["cyc_ms"] for r in rs if r["cyc_ms"] is not None)
        t_lo, t_hi = w * 10.0, min((w + 1) * 10.0, seg_wall_s)
        fc = lc = None
        for r in rs:
            if fc is None:
                fc = r["win_cpu_cum_ms"]
            lc = r["win_cpu_cum_ms"]
        occ = ((lc - fc) / 1000.0 / max(t_hi - t_lo, 1e-9) * 100.0
               if (fc is not None and lc is not None) else None)
        trend.append({"window": w, "t_lo_s": t_lo, "t_hi_s": t_hi,
                      "n": len(vals),
                      "median_ms": pct(vals, 50),
                      "max_ms": vals[-1] if vals else None,
                      "occupancy_pct_singlecore_filetime": occ})
    for t in trend:
        print("trend w%02d [%5.1f-%5.1fs] n=%3d med=%.3fms max=%.3fms occ=%.1f%%" %
              (t["window"], t["t_lo_s"], t["t_hi_s"], t["n"],
               t["median_ms"] or -1, t["max_ms"] or -1,
               t["occupancy_pct_singlecore_filetime"] or -1))
    n_w = len(trend)
    first_third = [t for t in trend if t["window"] < n_w / 3.0]
    last_third = [t for t in trend if t["window"] >= 2.0 * n_w / 3.0]
    med_f = statistics.median([t["median_ms"] for t in first_third]) \
        if first_third else None
    med_l = statistics.median([t["median_ms"] for t in last_third]) \
        if last_third else None
    rising = bool(med_f is not None and med_l is not None and med_f > 0
                  and med_l > med_f * 1.2)
    print("trend: first-third med=%.3f last-third med=%.3f ratio=%.3f rising=%s" %
          (med_f or -1, med_l or -1,
           (med_l / med_f) if (med_f and med_l) else -1, rising))

    # ---------- 拍间隔分布与 A 对照 ----------
    ivals = sorted(r["interval_ms"] for r in d1
                   if r.get("interval_ms") is not None)
    int_dist = dist_stats(ivals)
    int_dist["ge64ms"] = sum(1 for v in ivals if v >= 64.0)
    print("tick interval: n=%d median=%.3f p90=%.3f p99=%.3f max=%.3f "
          ">=64ms=%d (A: mean 32.000, >=64ms=0)" %
          (int_dist["n"], int_dist["median_ms"], int_dist["p90_ms"],
           int_dist["p99_ms"], int_dist["max_ms"], int_dist["ge64ms"]))

    # ---------- CPU vs 间隔（只描述） ----------
    pairs = [(r["cyc_ms"], r["interval_ms"]) for r in d1
             if r["cyc_ms"] is not None and r.get("interval_ms") is not None]
    r_p = pearson([p[0] for p in pairs], [p[1] for p in pairs]) if pairs else None
    r_s = spearman([p[0] for p in pairs], [p[1] for p in pairs]) if pairs else None
    print("cpu(cyc) vs interval: n=%d pearson=%s spearman=%s (describe only)" %
          (len(pairs), r_p, r_s))

    # ---------- 候选字段变化（只描述，不当单位数） ----------
    def field_summary(key):
        vals = [r.get(key) for r in ok_rows if r.get(key) is not None]
        if not vals:
            return {"n": 0}
        return {"n": len(vals),
                "first": vals[0], "last": vals[-1],
                "min": min(vals), "max": max(vals),
                "n_distinct": len(set(vals)),
                "first_nonzero_or_change": next(
                    (v for i, v in enumerate(vals)
                     if i > 0 and v != vals[0]), None)}
    fld_b = field_summary("B0CE88")
    fld_c = field_summary("87E8E0")
    print("B0CE88: %s" % fld_b)
    print("87E8E0: %s" % fld_c)

    # ---------- 零输入核对 ----------
    last_inputs = [r.get("last_input_dwtime") for r in watcher
                   if r.get("kind") == "ui_watch"
                   and r.get("t_mono_ns") is not None
                   and t0 <= r["t_mono_ns"] <= t1
                   and r.get("last_input_dwtime") is not None]
    zero_input = len(set(last_inputs)) <= 1 if last_inputs else None
    fg_true = sum(1 for s in seg if s.get("win_foreground"))
    print("zero-input check: watcher_scans_in_seg=%d distinct_last_input=%s "
          "fg_true=%d/%d" % (len(last_inputs), len(set(last_inputs)),
                             fg_true, len(seg)))

    # ---------- df≥2 ----------
    print("multi-tick events (df>=2): %d" % len(dmulti))
    for r in dmulti[:10]:
        print("  t=%7.3fs cpu=%7.3fms df=%s frame=%s int=%.2fms hiccup=%s" %
              (r["t_rel_s"], r["cpu_ms"], r["df"], r["frame"],
               r["interval_ms"] or -1, r["hiccup"]))

    # ---------- ★ 四臂对照与结论分档（预设判据，不得事后改） ----------
    b_med = cyc_dist["median_ms"]
    a_med = A_BASE["cycle_median_ms_per_tick"]
    rel_med = ((b_med - a_med) / a_med) if (b_med is not None and a_med) else None
    b_occ = occ_cyc if occ_cyc is not None else occ_ft
    a_occ = A_BASE["occupancy_pct_singlecore"]
    rel_occ = ((b_occ - a_occ) / a_occ) if (b_occ is not None and a_occ) else None

    combat_signal = bool(first_nz_ingame is not None
                         or (ev_bullet and (ev_bullet[0].get("detail") or {})
                             .get("phase") == "ingame"))
    early_end = meta.get("phase_stop") not in ("target_reached",) \
        and meta.get("phase_stop") is not None
    natural_end_t = (meta.get("sampling") or {}).get("natural_end_t_mono_ns")

    if not entered or seg_wall_s < VERDICT_SEG_MIN_S:
        tier = "[数据不足]"
        cpu_tier = "[数据不足]"
    else:
        if (b_med is not None and b_med > VERDICT_THRESH_MS) \
                or (b_occ is not None and b_occ > VERDICT_THRESH_OCC):
            cpu_tier = "[CPU 显著抬升]"
        elif rel_med is not None and MID_LO <= rel_med <= MID_HI:
            cpu_tier = "[中间地带]"
        elif rel_med is not None and rel_med > MID_HI:
            cpu_tier = "[CPU 显著抬升]"
        else:
            cpu_tier = "[无显著差异]"
        if combat_signal:
            tier = "[观测到战斗信号] × " + cpu_tier
        else:
            tier = cpu_tier

    print("=== A/W20 对照 ===")
    print("A: cycle med=%.3f ms occ=%.2f%% | W20: cycle med=%s ms occ=%s%%" %
          (a_med, a_occ, b_med, b_occ))
    print("median rel change = %+.1f%% | occupancy rel change = %+.1f%%" %
          ((rel_med or 0) * 100.0, (rel_occ or 0) * 100.0))
    print("combat_signal(0xA8ED50 nonzero) = %s" % combat_signal)

    # ---------- ★ 四臂对照表（A / HexBay / U800 / W20；本卡必交付） ----------
    four_arm = {
        "A_w15_proving_grounds": {
            "declared": "52 建筑 / 0 车 / 0 步兵（近空图）——本卡同载体",
            "cycle_median_ms": a_med,
            "occupancy_pct_singlecore": a_occ,
            "rel_vs_A_pct": 0.0,
            "cyc_per_ms": A_BASE["cyc_per_ms_w15_corrected"],
            "tick_rate_cps": A_BASE["tick_rate_counts_per_s"],
            "a8ed50": "全程 0",
            "tier_at_test_time": "无退化基线",
        },
        "HexBay_w18": {
            "declared": "144 建筑（可达上限）",
            "cycle_median_ms": HEXBAY_BASE["cycle_median_ms_per_tick"],
            "occupancy_pct_singlecore": HEXBAY_BASE["occupancy_pct_singlecore"],
            "rel_vs_A_pct": HEXBAY_BASE["rel_change_vs_a_median_pct"],
            "cyc_per_ms": HEXBAY_BASE["cyc_per_ms_selfcalibrated"],
            "tick_rate_cps": HEXBAY_BASE["whole_segment_cps"],
            "a8ed50": "全程 0",
            "tier": HEXBAY_BASE["tier"],
        },
        "U800_w19": {
            "declared": "0 建筑 / 480 车 / 320 步兵（声明合计 800，全库最高）",
            "cycle_median_ms": U800_BASE["cycle_median_ms_per_tick"],
            "occupancy_pct_singlecore": U800_BASE["occupancy_pct_singlecore"],
            "rel_vs_A_pct": U800_BASE["rel_change_vs_a_median_pct"],
            "cyc_per_ms": U800_BASE["cyc_per_ms_selfcalibrated"],
            "tick_rate_cps": U800_BASE["whole_segment_cps"],
            "a8ed50": "全程 0",
            "tier": U800_BASE["tier"],
        },
        "W20_combat": {
            "declared": "52 建筑 / 0 车 / 0 步兵（同 A 载体）；新变量 = 零输入 600 s "
                        "（AI 自然行为不被玩家干预）",
            "cycle_median_ms": b_med,
            "occupancy_pct_singlecore": b_occ,
            "rel_vs_A_pct": (rel_med * 100.0) if rel_med is not None else None,
            "cyc_per_ms": cyc_per_ms_b,
            "tick_rate_cps": cps_whole,
            "a8ed50_nonzero": combat_signal,
            "tier": tier,
        },
        "note": "中位 ms 各臂用各自全段自标定 cyc/ms 换算，臂间系数差异如实并列；"
                "占用率=窗口线程 ΔCPU/有效墙钟（单核%）。",
    }
    print("=== 四臂对照（A / HexBay / U800 / W20）===")
    print("臂        声明量                      cycle中位(ms)  occ(%)   vs A(中位)  A8ED50")
    print("A(W15)    52 建筑                      %-13.3f %-8.2f 基线        全程0" %
          (a_med, a_occ))
    print("HexBay    144 建筑（可达上限）          %-13.3f %-8.2f %+.1f%%       全程0" %
          (HEXBAY_BASE["cycle_median_ms_per_tick"],
           HEXBAY_BASE["occupancy_pct_singlecore"],
           HEXBAY_BASE["rel_change_vs_a_median_pct"]))
    print("U800(W19) 480 车+320 步兵（声明 800）   %-13.3f %-8.2f %+.1f%%       全程0" %
          (U800_BASE["cycle_median_ms_per_tick"],
           U800_BASE["occupancy_pct_singlecore"],
           U800_BASE["rel_change_vs_a_median_pct"]))
    print("W20       52 建筑+零输入600s            %-13s %-8s %s        %s" %
          ("%.3f" % b_med if b_med is not None else "n/a",
           "%.2f" % b_occ if b_occ is not None else "n/a",
           "%+.1f%%" % (rel_med * 100.0) if rel_med is not None else "n/a",
           "非零" if combat_signal else "全程0"))
    print("TIER:", tier)
    print("early_end=%s phase_stop=%s natural_end=%s" %
          (early_end, meta.get("phase_stop"), bool(natural_end_t)))

    # ---------- 落盘 ----------
    with open(OUT / "tickcost.csv", "w", encoding="utf-8", newline="") as f:
        wcsv = csv.writer(f)
        wcsv.writerow(["idx", "t_rel_s", "interval_ms", "cyc_est_ms",
                       "cyc_est_ms_A_factor", "cpu_ms_filetime", "frame",
                       "mode", "fg", "df", "gap", "hiccup", "win_cyc_delta",
                       "win_cpu_cum_ms", "win_kernel_cum_ms",
                       "win_user_cum_ms", "ctx", "A8ED50", "B0CE88",
                       "87E8E0", "note"])
        for r in rows:
            wcsv.writerow([
                r.get("idx"), round(r.get("t_rel_s") or 0, 6),
                (round(r["interval_ms"], 4)
                 if r.get("interval_ms") is not None else None),
                (round(r["cyc_ms"], 6) if r.get("cyc_ms") is not None else None),
                (round(r["cyc_ms_A_factor"], 6)
                 if r.get("cyc_ms_A_factor") is not None else None),
                (round(r["cpu_ms"], 6) if r.get("cpu_ms") is not None else None),
                r.get("frame"), r.get("mode"), r.get("fg"), r.get("df"),
                int(bool(r.get("gap"))), int(bool(r.get("hiccup"))),
                r.get("win_cyc_delta"),
                (round(r["win_cpu_cum_ms"], 6)
                 if r.get("win_cpu_cum_ms") is not None else None),
                r.get("win_kernel_cum_ms"), r.get("win_user_cum_ms"),
                r.get("ctx"), r.get("A8ED50"), r.get("B0CE88"),
                r.get("87E8E0"), r.get("note") or ("gap" if r.get("gap") else "")])

    skirmish = None
    try:
        skirmish = json.loads((OUT / "skirmish_settings.json")
                              .read_text(encoding="utf-8"))
    except Exception:
        skirmish = None

    analysis = {
        "card": "RE-N04i W20 combat dimension (zero-input 600s on [8] Proving Grounds)",
        "a_arm_baseline": A_BASE,
        "meta_run": {k: meta.get(k) for k in
                     ("pid", "is32", "game_tid", "map", "skirmish_settings",
                      "skirmish_settings_error", "phase_stop", "error",
                      "getprocesstimes_probe", "n_samples", "n_read_fail",
                      "n_winthread_fail", "started_utc", "ended_utc",
                      "carrier")},
        "segment": {"start_t_mono_ns": t0, "end_t_mono_ns": t1,
                    "wall_s": seg_wall_s, "n_ok_samples": len(seg),
                    "n_post_end_samples": len(post), "fg_true": fg_true,
                    "sampling_interval": samp_int,
                    "n_read_fail": meta.get("n_read_fail"),
                    "n_winthread_fail": meta.get("n_winthread_fail")},
        "map_entry": {"rule": "frame ≈29–32 计数/s 持续 ≥60 s；mode 仅旁证",
                      "entered": entered,
                      "whole_segment_cps": cps_whole,
                      "cps_per_10s_window": win_cps,
                      "cps_median": cps_med, "cps_min": cps_min,
                      "cps_max": cps_max},
        "cycle_calibration": {"cyc_per_ms_W20": cyc_per_ms_b,
                              "cyc_per_ms_A_w15_card": 3.104e9,
                              "cyc_per_ms_A_w15_card_unit_note":
                                  "卡面 3.104e9 实为 cyc/s（≈3.104 GHz），写成 cyc/ms 是单位勘误；"
                                  "各臂判读均用各自全段自标定（ms 口径），不受影响",
                              "cyc_per_ms_A_w15_corrected": 3.104e6,
                              "cyc_per_ms_HexBay_w18_selfcal": HEXBAY_BASE["cyc_per_ms_selfcalibrated"],
                              "cyc_per_ms_U800_w19_selfcal": U800_BASE["cyc_per_ms_selfcalibrated"],
                              "ratio_W20_over_A_corrected": (cyc_per_ms_b / 3.104e6)
                              if cyc_per_ms_b else None},
        "per_tick_cpu_cycle_primary": cyc_dist,
        "per_tick_cpu_cycle_histogram_1ms": hist1,
        "per_tick_cpu_filetime_crosscheck": ft_dist,
        "quantum": quantum,
        "occupancy": {"window_thread_cycle_pct": occ_cyc,
                      "window_thread_filetime_pct": occ_ft,
                      "unit": "单核百分比；CPU 不含阻塞等待"},
        "a8ed50_timeline": a8_timeline,
        "combat_contrast_60s": combat_contrast,
        "a8ed50_conditional_cpu": cond_cpu,
        "a8ed50_value_buckets": val_table,
        "fg_effect": fg_effect,
        "window_contrast_quiet_vs_heavy": window_contrast,
        "seg60": {"windows": seg60,
                  "seg0_median_ms": med_seg0,
                  "rising_candidates_vs_seg0_gt20pct": rising_segs,
                  "rule": "60 s 段中位；>+20% vs seg0 ⇒ 上升候选"},
        "a_vs_w20": {
            "median_cycle_ms": {"A": a_med, "W20": b_med,
                                "rel_change_pct": (rel_med * 100.0)
                                if rel_med is not None else None},
            "occupancy_pct": {"A": a_occ, "W20": b_occ,
                              "rel_change_pct": (rel_occ * 100.0)
                              if rel_occ is not None else None},
            "tick_interval": {"A_mean_ms": A_BASE["tick_interval_mean_ms"],
                              "A_ge64ms": A_BASE["tick_interval_ge64ms"],
                              "W20": int_dist},
            "tick_rate_cps": {"A": A_BASE["tick_rate_counts_per_s"],
                              "W20_whole_segment": cps_whole},
        },
        "four_arm": four_arm,
        "hotspots_cycle": {"rule": ">=3x median AND >=1.0ms (df=1, cycle)",
                           "median_ms": med_c, "n_candidates": len(hot),
                           "top20": [{k: r.get(k) for k in
                                      ("t_rel_s", "cyc_ms", "frame", "mode",
                                       "fg", "interval_ms", "idx", "A8ED50")}
                                     for r in hot[:20]]},
        "trend_10s": {"windows": trend,
                      "first_third_median_ms": med_f,
                      "last_third_median_ms": med_l,
                      "ratio": (med_l / med_f) if (med_f and med_l) else None,
                      "rising_candidate": rising,
                      "rule": "末1/3窗中位 > 首1/3窗中位 × 1.2"},
        "tick_interval_distribution": int_dist,
        "cpu_vs_interval": {"n": len(pairs), "pearson": r_p,
                            "spearman": r_s, "note": "只描述相关，不归因"},
        "candidate_fields": {"B0CE88": fld_b, "87E8E0": fld_c,
                             "probe_event": (ev_bullet[0].get("detail")
                                             if ev_bullet else None),
                             "note": "B0CE88/87E8E0 语义未定，只描述不当单位数；"
                                     "0xA8ED50 候选 BulletCnt 语义未证，只作开战旁证"},
        "skirmish_settings_available": skirmish is not None,
        "zero_input": {"watcher_scans_in_seg": len(last_inputs),
                       "distinct_last_input": len(set(last_inputs)),
                       "ok": zero_input},
        "multi_tick_events": [{"t_rel_s": r.get("t_rel_s"),
                               "cpu_ms": r.get("cpu_ms"), "df": r.get("df"),
                               "frame": r.get("frame"),
                               "interval_ms": r.get("interval_ms"),
                               "hiccup": r.get("hiccup")} for r in dmulti],
        "gap_rows_n": len(gap_rows),
        "early_end": early_end,
        "combat_signal": combat_signal,
        "cpu_tier": cpu_tier,
        "tier": tier,
    }
    (OUT / "analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=1, default=str),
        encoding="utf-8")
    print("written: analysis.json, tickcost.csv (%d rows)" % len(rows))
    return 0


def _dump_min(out, tier, extra):
    (out / "analysis.json").write_text(
        json.dumps({"tier": tier, **extra}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("written minimal analysis.json")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
