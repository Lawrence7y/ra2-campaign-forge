#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""NEXT_RE_20261112_R02 / W18 —— RE-N04g 高建筑载体 B′（HexBay）负载对照离线重算。

输入：W18_load_HexBay/out/run.ndjson + ui_watch.ndjson + meta.json
输出：W18_load_HexBay/out/analysis.json + W18_load_HexBay/out/tickcost.csv + stdout 摘要

★ 主判读通道 = cycle（QueryThreadCycleTime）；FILETIME 仅交叉核对（本机
  GetThreadTimes 记账量子 15.625 ms，W15 实测 828 个非零 Δ 全为该值——
  中位 0 是量子产物，不得读作"拍快"）。
★ cycle→ms 标定：cyc_per_ms = Σ(逐拍 cycle Δ) / Σ(逐拍 FILETIME Δ CPU ms)
  （全段长窗标定，量子抵消；本卡实测 B′ = 3.311e6 cyc/ms ≈ 3.311 GHz）。
  ★ 口径勘误（W18 发现，如实记录）：W15 卡面写"A 臂 ≈3.104e9 cyc/ms"，该值实为
  **cyc/s**（≈3.104 GHz 时钟频率）；正确 cyc/ms 口径 = 3.104e6。W15/W17 的判读
  均用各自全段自标定（ms 口径），不受此勘误影响；仅"用 A 系数换算的旁证列
  cyc_ms_A_factor"在此前卡中偏小 1000 倍，本卡已修正（除数 3.104e6 cyc/ms）。
★ 预设判据（卡面固定，不得事后改）：
  进图成功 = frame 以 ≈29–32 计数/s 持续 ≥60 s（mode 仅旁证）。
  [成功造出压力] = B cycle 每拍中位 > 2.54 ms（=A 1.691×1.5）或占用率 > 10%；
  [无显著差异]   = 相对 A 差 < 20%；
  [中间地带]     = 20%–50%（如实报告，不强行归类；方向相反的差异也如实报告）；
  [B′ 不可用]     = 未进图或有效段 < 90 s（不重启凑时长）。
★ A 臂基线（W15 实测）：cycle 中位 1.691 ms/拍；FILETIME 均值 1.725 ms；
  占用率 5.39% 单核；拍率 31.2492 计数/s；拍间隔均值 32.000 ms、≥64 ms 间隔 0。
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

W18 = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W18_load_HexBay")
OUT = W18 / "out"
NS_MS = 1e6

# A 臂基线（W15 实测；开工前固定）
A_BASE = {
    "carrier": "[8]试验地_Pro_ProvingGrounds.yrm ([8] Proving Grounds)",
    "cycle_median_ms_per_tick": 1.691,
    "filetime_mean_ms_per_tick": 1.725,
    "occupancy_pct_singlecore": 5.39,
    "tick_rate_counts_per_s": 31.2492,
    "tick_interval_mean_ms": 32.000,
    "tick_interval_ge64ms": 0,
    "cyc_per_ms_w15": 3.104e9,          # W15 卡面原值（实为 cyc/s，≈3.104 GHz 时钟频率）
    "cyc_per_ms_w15_corrected": 3.104e6,  # 口径修正：cyc/s → cyc/ms（卡面单位勘误）
    "ingame_s": 240.006,
}
VERDICT_THRESH_MS = 2.54       # A 中位 × 1.5
VERDICT_THRESH_OCC = 10.0      # 单核 %


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
    print("carrier: %s %s B sha=%s" %
          ((meta.get("carrier") or {}).get("bytes"),
           (meta.get("carrier") or {}).get("expected_bytes"),
           (meta.get("carrier") or {}).get("sha256")))

    # ---------- 有效局内段 ----------
    seg = [s for s in samples if s.get("phase") == "ingame"
           and s.get("read_status") == "ok"]
    post = [s for s in samples if s.get("phase") == "post_end"]
    if not seg:
        print("!! 无 ingame ok 采样 ⇒ 未进图 ⇒ [B′ 不可用]")
        verdict = "[B′ 不可用]"
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

    # ---------- 递增事件与 CPU 归属（与 W15 完全同规则） ----------
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
    print("cycle calibration: tot_cyc=%.4g tot_cpu=%.3fms cyc_per_ms_B=%.4g "
          "(A/W15 corrected=3.104e6 cyc/ms [卡面 3.104e9 为 cyc/s，勘误], ratio=%.4f)" %
          (tot_cyc, tot_cpu, cyc_per_ms_b or -1,
           (cyc_per_ms_b / A_BASE["cyc_per_ms_w15_corrected"]) if cyc_per_ms_b else -1))

    # ---------- 每拍 CPU：cycle 主判读 + FILETIME 交叉核对 ----------
    for r in d1:
        r["cyc_ms"] = (r["win_cyc_delta"] / cyc_per_ms_b
                       if (cyc_per_ms_b and r.get("win_cyc_delta") is not None)
                       else None)
        # A 系数旁证列：卡面 3.104e9 为 cyc/s（单位勘误），cyc/ms 口径 = 3.104e6
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
          (ft_dist["n"], ft_dist["min_ms"], ft_dist["median_ms"],
           ft_dist["p90_ms"], ft_dist["p99_ms"], ft_dist["max_ms"],
           ft_dist["mean_ms"]))
    hist1 = histogram(cyc_vals, 1.0)
    print("cycle histogram (1ms bins):", {k: v for k, v in hist1.items()})

    # ---------- 进图判定：帧率（预设 ≈29–32 计数/s 持续 ≥60 s） ----------
    win_cps = []
    w_by_10s = {}
    for r in d1:
        w = int(r["t_rel_s"] // 10)
        w_by_10s.setdefault(w, []).append(r)
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

    # ---------- 热点候选（cycle 通道；沿用 W15 判据作旁证参考） ----------
    med_c = cyc_dist["median_ms"] or 0.0
    hot = [r for r in d1 if r["cyc_ms"] is not None
           and r["cyc_ms"] >= 3.0 * med_c and r["cyc_ms"] >= 1.0]
    hot.sort(key=lambda r: -r["cyc_ms"])
    print("cycle hotspots (>=3x med AND >=1.0ms): %d hits" % len(hot))
    for r in hot[:20]:
        print("  t=%7.3fs cyc~%7.3fms frame=%s mode=%s fg=%s int=%.2fms" %
              (r["t_rel_s"], r["cyc_ms"], r["frame"], r["mode"], r["fg"],
               r["interval_ms"] or -1))

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

    # ---------- 趋势（10 s 窗，cycle 通道 + 占用率通道） ----------
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
    occ_f = statistics.median([t["occupancy_pct_singlecore_filetime"]
                               for t in first_third
                               if t["occupancy_pct_singlecore_filetime"]
                               is not None]) if first_third else None
    occ_l = statistics.median([t["occupancy_pct_singlecore_filetime"]
                               for t in last_third
                               if t["occupancy_pct_singlecore_filetime"]
                               is not None]) if last_third else None
    rising = bool(med_f is not None and med_l is not None and med_f > 0
                  and med_l > med_f * 1.2)
    rising_occ = bool(occ_f is not None and occ_l is not None
                      and occ_l > occ_f * 1.2)
    print("trend: first-third med=%.3f last-third med=%.3f ratio=%.3f rising=%s "
          "| occupancy-channel first=%.2f%% last=%.2f%% rising_occ=%s" %
          (med_f or -1, med_l or -1,
           (med_l / med_f) if (med_f and med_l) else -1, rising,
           occ_f or -1, occ_l or -1, rising_occ))

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

    # ---------- 候选字段变化（只描述） ----------
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
    fld_a = field_summary("A8ED50")
    fld_b = field_summary("B0CE88")
    fld_c = field_summary("87E8E0")
    seq_vals = [r.get("A8ED50") for r in ok_rows]
    first_nz_ingame = None
    for r in ok_rows:
        v = r.get("A8ED50")
        if v is not None and v != 0:
            first_nz_ingame = {"t_rel_s": r["t_rel_s"], "value": v,
                               "frame": r["frame"]}
            break
    print("A8ED50: %s" % fld_a)
    print("A8ED50 first nonzero in ingame: %s" % (first_nz_ingame or "从未非零"))
    print("B0CE88: %s" % fld_b)
    print("87E8E0: %s" % fld_c)
    ev_bullet = [e for e in events if e.get("event") == "a8ed50_first_nonzero"]
    print("probe events a8ed50_first_nonzero: %s" %
          (ev_bullet[0].get("detail") if ev_bullet else "none"))

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

    # ---------- ★ A 臂对照与结论分档（预设判据，不得事后改） ----------
    b_med = cyc_dist["median_ms"]
    a_med = A_BASE["cycle_median_ms_per_tick"]
    rel_med = ((b_med - a_med) / a_med) if (b_med is not None and a_med) else None
    b_occ = occ_cyc if occ_cyc is not None else occ_ft
    a_occ = A_BASE["occupancy_pct_singlecore"]
    rel_occ = ((b_occ - a_occ) / a_occ) if (b_occ is not None and a_occ) else None

    early_end = meta.get("phase_stop") not in ("target_reached",) \
        and meta.get("phase_stop") is not None
    natural_end_t = (meta.get("sampling") or {}).get("natural_end_t_mono_ns")

    if not entered or seg_wall_s < 90.0:
        tier = "[B′ 不可用]"
    elif (b_med is not None and b_med > VERDICT_THRESH_MS) \
            or (b_occ is not None and b_occ > VERDICT_THRESH_OCC):
        tier = "[成功造出压力]"
    elif rel_med is not None and abs(rel_med) < 0.20:
        tier = "[无显著差异]"
    else:
        tier = "[中间地带]"

    print("=== A/B 对照 ===")
    print("A: cycle med=%.3f ms occ=%.2f%% | B: cycle med=%s ms occ=%s%%" %
          (a_med, a_occ, b_med, b_occ))
    print("median rel change = %+.1f%% | occupancy rel change = %+.1f%%" %
          ((rel_med or 0) * 100.0, (rel_occ or 0) * 100.0))
    print("TIER:", tier)
    print("early_end=%s phase_stop=%s natural_end=%s" %
          (early_end, meta.get("phase_stop"),
           bool(natural_end_t)))

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

    analysis = {
        "card": "RE-N04g W18 load-B' arm (HexBay, single-variable map swap)",
        "a_arm_baseline": A_BASE,
        "meta_run": {k: meta.get(k) for k in
                     ("pid", "is32", "game_tid", "map", "phase_stop", "error",
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
        "cycle_calibration": {"cyc_per_ms_B": cyc_per_ms_b,
                              "cyc_per_ms_A_w15_card": 3.104e9,
                              "cyc_per_ms_A_w15_card_unit_note":
                                  "卡面 3.104e9 实为 cyc/s（≈3.104 GHz），写成 cyc/ms 是单位勘误；"
                                  "W15/W18 判读均用各自全段自标定（ms 口径），不受影响",
                              "cyc_per_ms_A_w15_corrected": 3.104e6,
                              "ratio_B_over_A_corrected": (cyc_per_ms_b / 3.104e6)
                              if cyc_per_ms_b else None},
        "per_tick_cpu_cycle_primary": cyc_dist,
        "per_tick_cpu_cycle_histogram_1ms": hist1,
        "per_tick_cpu_filetime_crosscheck": ft_dist,
        "quantum": quantum,
        "occupancy": {"window_thread_cycle_pct": occ_cyc,
                      "window_thread_filetime_pct": occ_ft,
                      "unit": "单核百分比；CPU 不含阻塞等待"},
        "a_vs_b": {
            "median_cycle_ms": {"A": a_med, "B": b_med,
                                "rel_change_pct": (rel_med * 100.0)
                                if rel_med is not None else None},
            "occupancy_pct": {"A": a_occ, "B": b_occ,
                              "rel_change_pct": (rel_occ * 100.0)
                              if rel_occ is not None else None},
            "tick_interval": {"A_mean_ms": A_BASE["tick_interval_mean_ms"],
                              "A_ge64ms": A_BASE["tick_interval_ge64ms"],
                              "B": int_dist},
            "tick_rate_cps": {"A": A_BASE["tick_rate_counts_per_s"],
                              "B_whole_segment": cps_whole},
        },
        "hotspots_cycle": {"rule": ">=3x median AND >=1.0ms (df=1, cycle)",
                           "median_ms": med_c, "n_candidates": len(hot),
                           "top20": [{k: r.get(k) for k in
                                      ("t_rel_s", "cyc_ms", "frame", "mode",
                                       "fg", "interval_ms", "idx")}
                                     for r in hot[:20]]},
        "trend": {"windows_10s": trend,
                  "first_third_median_ms": med_f,
                  "last_third_median_ms": med_l,
                  "ratio": (med_l / med_f) if (med_f and med_l) else None,
                  "rising_candidate": rising,
                  "occupancy_first_third_pct": occ_f,
                  "occupancy_last_third_pct": occ_l,
                  "rising_occupancy_candidate": rising_occ,
                  "rule": "末1/3窗中位 > 首1/3窗中位 × 1.2"},
        "tick_interval_distribution": int_dist,
        "cpu_vs_interval": {"n": len(pairs), "pearson": r_p,
                            "spearman": r_s, "note": "只描述相关，不归因"},
        "candidate_fields": {"A8ED50": fld_a,
                             "A8ED50_first_nonzero_ingame": first_nz_ingame,
                             "B0CE88": fld_b, "87E8E0": fld_c,
                             "probe_event": (ev_bullet[0].get("detail")
                                             if ev_bullet else None),
                             "note": "语义未定，只描述变化"},
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
