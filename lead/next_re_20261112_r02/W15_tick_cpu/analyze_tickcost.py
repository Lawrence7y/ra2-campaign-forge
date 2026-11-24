#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""NEXT_RE_20261112_R02 / W15 —— 每拍 CPU 成本离线重算（RE-N04e）。

输入：W15/out/run.ndjson（探针采样）+ W15/out/ui_watch.ndjson（观察者）+ meta.json
输出：W15/out/analysis.json + W15/out/tickcost.csv + 本 stdout 摘要

★ 预设判据（与探针 meta.predeclared_analysis_plan 一致，开工前固定，不得事后改）：
  * 归属：每拍成本 = 相邻两次 frame 递增采样之间 Δ(win_kernel+win_user)。
    归属窗口 = 1 拍 ± 采样量化（±~6 ms）；窗口线程 CPU 含渲染+消息泵+逻辑。
  * 分布主表用 df=1（Δframe=1）事件；df≥2 全额记单行并标注，不摊分。
  * 热点候选：每拍 CPU ≥ 3×中位 且 ≥ 1.0 ms ⇒ 前 20 名。
  * 趋势：10 s 窗 median(每拍CPU)；末 1/3 窗中位 > 首 1/3 窗中位 × 1.2 ⇒ 上升候选。
  * CPU 占用率 = ΔCPU/有效墙钟；单位=单核百分比。CPU 时间不含阻塞等待；
    「一拍 CPU 低」≠「这一拍快」。
  * read_status=fail / win_thread_err 拍：跨其上的递增不计算 CPU（gap 标注）。
  * 量子：GetThreadTimes 记账受系统时钟节拍粒度约束；本文件实测每对相邻采样的
    非零 ΔCPU 的 distinct 值并报告量子（bindtest 自测已见 15.625 ms 台阶，
    游戏若请求更高计时分辨率则可能更细——以实测为准）。
  * 结论分档优先级（预设）：[数据不足]（有效段<90s）> [存在热点候选] >
    [CPU 成本上升趋势] > [未发现热点候选]。热点与趋势同时成立时热点为主档、
    趋势为副档并如实并列。
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from pathlib import Path

W15 = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W15_tick_cpu")
OUT = W15 / "out"
NS_MS = 1e6


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
    """线性插值百分位（sorted_vals 非空）。"""
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


def histogram(vals, bin_ms=1.0, max_bins=48):
    if not vals:
        return {}
    hi = min(max(vals) + bin_ms, bin_ms * max_bins)
    bins = {}
    for v in vals:
        b = min(int(v / bin_ms), max_bins - 1) * bin_ms
        bins[b] = bins.get(b, 0) + 1
    return {("%g-%g" % (b, min(b + bin_ms, hi))): bins[b]
            for b in sorted(bins.keys())}


def main():
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None,
                    help="覆盖 out 目录（合成数据自测用；默认 W15/out）")
    a = ap.parse_args()
    if a.dir:
        OUT = Path(a.dir)
    samples = [r for r in load_ndjson(OUT / "run.ndjson")
               if r.get("kind") == "sample"]
    events = [r for r in load_ndjson(OUT / "run.ndjson")
              if r.get("kind") == "event"]
    watcher = load_ndjson(OUT / "ui_watch.ndjson")
    meta = json.loads((OUT / "meta.json").read_text(encoding="utf-8"))

    print("samples=%d events=%d watcher=%d" % (len(samples), len(events), len(watcher)))
    print("meta: pid=%s map=%s phase_stop=%s err=%s" %
          (meta.get("pid"), (meta.get("map") or {}).get("display_name"),
           meta.get("phase_stop"), meta.get("error")))

    # ---------- 有效局内段 ----------
    seg = [s for s in samples if s.get("phase") == "ingame"
           and s.get("read_status") == "ok"]
    post = [s for s in samples if s.get("phase") == "post_end"]
    if not seg:
        print("!! 无 ingame ok 采样，判 [数据不足]")
        return 1
    t0 = seg[0]["t_mono_ns"]
    t1 = seg[-1]["t_mono_ns"]
    seg_wall_s = (t1 - t0) / 1e9
    for s in seg:
        s["_t_rel_s"] = (s["t_mono_ns"] - t0) / 1e9

    # 采样间隔实测（ingame ok 段）
    ints = [s["interval_ms_actual"] for s in seg
            if s.get("interval_ms_actual") is not None]
    ints_sorted = sorted(ints)
    samp_int = {
        "n": len(ints),
        "min_ms": ints_sorted[0] if ints else None,
        "median_ms": pct(ints_sorted, 50),
        "p90_ms": pct(ints_sorted, 90),
        "p99_ms": pct(ints_sorted, 99),
        "max_ms": ints_sorted[-1] if ints else None,
        "mean_ms": (sum(ints) / len(ints)) if ints else None,
        "over20_ms": sum(1 for v in ints if v > 20.0),
    }
    print("sampling interval: n=%d median=%.3f p90=%.3f p99=%.3f max=%.3f >20ms=%d" %
          (samp_int["n"], samp_int["median_ms"], samp_int["p90_ms"],
           samp_int["p99_ms"], samp_int["max_ms"], samp_int["over20_ms"]))

    # ---------- 递增事件与 CPU 归属（单遍扫描；基线=上次递增采样，卡面归属规则） ----------
    hiccup_thresh = max(3.0 * (samp_int["median_ms"] or 6.0), 24.0)
    all_by_seq = {s["seq"]: s for s in samples}
    rows = []
    prev_ev = None          # 上次递增采样（归属基线；首次=局内段前最后 ok 采样）
    seen_first_ingame = False
    for s in samples:
        if s.get("phase") == "post_end":
            break           # 有效局内段之外不再归属
        ok = (s.get("read_status") == "ok" and s.get("win_cpu_ms") is not None
              and not s.get("win_thread_err"))
        if s.get("phase") == "ingame":
            seen_first_ingame = True
        if not seen_first_ingame:
            # 局内段之前只跟随 ok 基线（加载期 frame 恒 0）
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
                seq_lo = prev_ev["seq"]
                seq_hi = s["seq"]
                gap = False
                gap_cause = None
                worst_bracket = None
                hiccup = False
                for q in range(seq_lo + 1, seq_hi + 1):
                    qq = all_by_seq.get(q)
                    if qq is None:
                        continue
                    if qq.get("read_status") != "ok" \
                            or qq.get("win_cpu_ms") is None \
                            or qq.get("win_thread_err"):
                        gap = True
                        gap_cause = "read_fail_or_winthread_err_between"
                    if qq.get("interval_ms_actual") is not None:
                        if qq["interval_ms_actual"] > hiccup_thresh:
                            hiccup = True
                        if worst_bracket is None \
                                or qq["interval_ms_actual"] > worst_bracket:
                            worst_bracket = qq["interval_ms_actual"]
                cyc = None
                if (s.get("win_cycle") is not None
                        and prev_ev.get("win_cycle") is not None):
                    cyc = s["win_cycle"] - prev_ev["win_cycle"]
                rows.append({
                    "idx": len(rows) + 1,
                    "t_rel_s": (s["t_mono_ns"] - t0) / 1e9,
                    "interval_ms": (s["t_mono_ns"] - prev_ev["t_mono_ns"]) / NS_MS,
                    "cpu_ms": s["win_cpu_ms"] - prev_ev["win_cpu_ms"],
                    "frame": f,
                    "mode": s.get("mode_A8B238"),
                    "fg": s.get("win_foreground"),
                    "df": f - pf,
                    "gap": gap,
                    "gap_cause": gap_cause,
                    "n_between_samples": seq_hi - seq_lo - 1,
                    "hiccup": hiccup,
                    "worst_bracket_ms": worst_bracket,
                    "win_cyc_delta": cyc,
                    "win_cpu_cum_ms": s["win_cpu_ms"],
                    "win_kernel_cum_ms": s.get("win_kernel_ms"),
                    "win_user_cum_ms": s.get("win_user_ms"),
                    "ctx": s.get("win_ctx_switches"),
                    "_seq": seq_hi,
                })
                prev_ev = s
            elif f < pf:
                rows.append({"idx": len(rows) + 1,
                             "t_rel_s": (s["t_mono_ns"] - t0) / 1e9,
                             "interval_ms": None, "cpu_ms": None, "frame": f,
                             "mode": s.get("mode_A8B238"),
                             "fg": s.get("win_foreground"),
                             "df": None, "gap": True,
                             "gap_cause": "frame_regression",
                             "note": "frame 回退（异常）"})
                prev_ev = s
            # f == pf：基线不动（prev_ev 只在递增事件上推进——卡面归属规则：
            # 每拍成本 = 本次递增采样与上次递增采样之间的 Δ；否则退化为逐样本差）
        # 非 ok 采样：保留在 all_by_seq 中参与 gap 判定，不作基线
    ok_rows = [r for r in rows if r.get("cpu_ms") is not None and not r["gap"]]
    d1 = [r for r in ok_rows if r.get("df") == 1]
    dmulti = [r for r in ok_rows if (r.get("df") or 0) >= 2]
    gap_rows = [r for r in rows if r["gap"] and r.get("cpu_ms") is None]
    print("events: total=%d ok=%d df1=%d df2+=%d gap=%d" %
          (len(rows), len(ok_rows), len(d1), len(dmulti), len(gap_rows)))

    cpu_vals = sorted(r["cpu_ms"] for r in d1)
    dist = {
        "n_df1": len(d1),
        "min_ms": cpu_vals[0] if cpu_vals else None,
        "median_ms": pct(cpu_vals, 50),
        "p90_ms": pct(cpu_vals, 90),
        "p99_ms": pct(cpu_vals, 99),
        "max_ms": cpu_vals[-1] if cpu_vals else None,
        "mean_ms": (sum(cpu_vals) / len(cpu_vals)) if cpu_vals else None,
    }
    print("per-tick CPU (df=1): min=%.3f med=%.3f p90=%.3f p99=%.3f max=%.3f mean=%.3f" %
          (dist["min_ms"], dist["median_ms"], dist["p90_ms"], dist["p99_ms"],
           dist["max_ms"], dist["mean_ms"]))
    print("histogram (1ms bins):", histogram(cpu_vals))

    # ---------- 量子实测 ----------
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
    quantum = {
        "n_nonzero_pairs": len(nz),
        "distinct_nonzero_first12": distinct[:12],
        "min_nonzero_ms": distinct[0] if distinct else None,
        "all_multiple_of_15_625": (all(abs(v / 15.625 - round(v / 15.625)) < 0.01
                                       for v in distinct) if distinct else None),
    }
    print("quantum check: nonzero_pairs=%d distinct[:12]=%s" %
          (quantum["n_nonzero_pairs"], quantum["distinct_nonzero_first12"]))

    # ---------- 热点候选（预设判据） ----------
    med = dist["median_ms"] or 0.0
    hot = [r for r in d1 if r["cpu_ms"] >= 3.0 * med and r["cpu_ms"] >= 1.0]
    hot.sort(key=lambda r: -r["cpu_ms"])
    hot_top = hot[:20]
    print("hotspot candidates (>=3x med AND >=1.0ms): %d hits" % len(hot))
    for r in hot_top:
        print("  t=%7.3fs cpu=%7.3fms frame=%s mode=%s fg=%s int=%.2fms" %
              (r["t_rel_s"], r["cpu_ms"], r["frame"], r["mode"], r["fg"],
               r["interval_ms"] or -1))

    # ---------- cycle 辅通道 ----------
    cyc_rows = [r for r in d1 if r.get("win_cyc_delta")]
    tot_cyc = sum(r["win_cyc_delta"] for r in cyc_rows)
    tot_cpu = sum(r["cpu_ms"] for r in cyc_rows)
    cyc_per_ms = (tot_cyc / tot_cpu) if tot_cpu > 0 else None
    cyc_hot = []
    if cyc_per_ms:
        cvals = sorted(r["win_cyc_delta"] / cyc_per_ms for r in cyc_rows)
        cmed = pct(cvals, 50) or 0.0
        cyc_hot = [r for r in cyc_rows
                   if r["win_cyc_delta"] / cyc_per_ms >= 3.0 * cmed
                   and r["win_cyc_delta"] / cyc_per_ms >= 1.0]
        cyc_hot.sort(key=lambda r: -(r["win_cyc_delta"] / cyc_per_ms))
        print("cycle channel: n=%d cyc_per_ms=%.0f med=%.3fms hot=%d" %
              (len(cyc_rows), cyc_per_ms, cmed, len(cyc_hot)))
        for r in cyc_hot[:20]:
            print("  [cyc] t=%7.3fs cpu~%7.3fms frame=%s mode=%s fg=%s" %
                  (r["t_rel_s"], r["win_cyc_delta"] / cyc_per_ms,
                   r["frame"], r["mode"], r["fg"]))

    # ---------- 趋势（10 s 窗） ----------
    win = {}
    for r in d1:
        w = int(r["t_rel_s"] // 10)
        win.setdefault(w, []).append(r["cpu_ms"])
    trend = []
    for w in sorted(win.keys()):
        vals = sorted(win[w])
        t_lo, t_hi = w * 10.0, min((w + 1) * 10.0, seg_wall_s)
        # 窗口占用率用累计值差（抗量子偏置）
        first_cum = None
        last_cum = None
        for r in ok_rows:
            if t_lo <= r["t_rel_s"] < t_hi:
                if first_cum is None:
                    first_cum = r["win_cpu_cum_ms"]
                last_cum = r["win_cpu_cum_ms"]
        occ = ((last_cum - first_cum) / 1000.0 / max(t_hi - t_lo, 1e-9) * 100.0
               if (first_cum is not None and last_cum is not None) else None)
        trend.append({"window": w, "t_lo_s": t_lo, "t_hi_s": t_hi,
                      "n": len(vals),
                      "median_ms": pct(vals, 50),
                      "max_ms": vals[-1] if vals else None,
                      "occupancy_pct_singlecore": occ})
    for t in trend:
        print("trend w%02d [%5.1f-%5.1fs] n=%3d med=%.3fms max=%.3fms occ=%.1f%%" %
              (t["window"], t["t_lo_s"], t["t_hi_s"], t["n"], t["median_ms"],
               t["max_ms"] or -1, t["occupancy_pct_singlecore"] or -1))
    n_w = len(trend)
    first_third = [t for t in trend if t["window"] < n_w / 3.0]
    last_third = [t for t in trend if t["window"] >= 2.0 * n_w / 3.0]
    med_f = statistics.median([t["median_ms"] for t in first_third]) \
        if first_third else None
    med_l = statistics.median([t["median_ms"] for t in last_third]) \
        if last_third else None
    rising = bool(med_f is not None and med_l is not None and med_f > 0
                  and med_l > med_f * 1.2)
    print("trend: first-third median=%s last-third median=%s ratio=%s rising=%s "
          "(rule: last > first x 1.2; med=0 时判据不可触发——量子所致，如实报告)" %
          (med_f, med_l,
           (med_l / med_f) if (med_f is not None and med_l is not None
                               and med_f > 0) else None, rising))

    # ---------- CPU 占用率（单核百分比） ----------
    win_cum = [s["win_cpu_ms"] for s in seg if s.get("win_cpu_ms") is not None]
    occ_win = ((win_cum[-1] - win_cum[0]) / 1000.0 / seg_wall_s * 100.0
               if len(win_cum) >= 2 else None)
    # 进程级：观察者 thread_sweep 求和
    sweeps = [r for r in watcher if r.get("kind") == "thread_sweep"
              and r.get("t_mono_ns") is not None
              and t0 - int(3e9) <= r["t_mono_ns"] <= t1 + int(3e9)]
    occ_proc = None
    proc_detail = None
    if len(sweeps) >= 2:
        s_a, s_b = sweeps[0], sweeps[-1]
        dt = (s_b["t_mono_ns"] - s_a["t_mono_ns"]) / 1e9
        if dt > 0:
            occ_proc = (s_b["sum_cpu_ms"] - s_a["sum_cpu_ms"]) / 1000.0 / dt * 100.0
            occ_proc_k = (s_b["sum_kernel_ms"] - s_a["sum_kernel_ms"]) / 1000.0 / dt * 100.0
            occ_proc_u = (s_b["sum_user_ms"] - s_a["sum_user_ms"]) / 1000.0 / dt * 100.0
            proc_detail = {"n_sweeps_in_seg": len(sweeps),
                           "wall_s": dt,
                           "occupancy_pct_singlecore": occ_proc,
                           "kernel_pct": occ_proc_k, "user_pct": occ_proc_u,
                           "sum_cpu_start_ms": s_a["sum_cpu_ms"],
                           "sum_cpu_end_ms": s_b["sum_cpu_ms"],
                           "n_threads_start": s_a.get("n_threads"),
                           "n_threads_end": s_b.get("n_threads"),
                           "retired_cpu_ms_total": s_b.get("retired_cpu_ms")}
    print("occupancy: window-thread=%.2f%% process=%.2f%% (single-core %%; CPU time "
          "excludes blocking waits)" %
          (occ_win or -1, (proc_detail or {}).get("occupancy_pct_singlecore") or -1))

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

    # ---------- 与拍间隔的对照 ----------
    pairs = [(r["cpu_ms"], r["interval_ms"]) for r in d1
             if r.get("interval_ms") is not None]
    r_p = pearson([p[0] for p in pairs], [p[1] for p in pairs]) if pairs else None
    r_s = spearman([p[0] for p in pairs], [p[1] for p in pairs]) if pairs else None
    print("cpu vs interval: n=%d pearson=%s spearman=%s (describe only, no attribution)" %
          (len(pairs), r_p, r_s))

    # ---------- df≥2 事件 ----------
    print("multi-tick events (df>=2): %d" % len(dmulti))
    for r in dmulti[:10]:
        print("  t=%7.3fs cpu=%7.3fms df=%s frame=%s int=%.2fms hiccup=%s" %
              (r["t_rel_s"], r["cpu_ms"], r["df"], r["frame"],
               r["interval_ms"] or -1, r["hiccup"]))

    # ---------- 结论分档（预设优先级） ----------
    if seg_wall_s < 90.0:
        tier = "[数据不足]"
    elif hot:
        tier = "[存在热点候选]"
    elif rising:
        tier = "[CPU 成本上升趋势]"
    else:
        tier = "[未发现热点候选]"
    print("TIER:", tier)

    # ---------- 落盘 ----------
    with open(OUT / "tickcost.csv", "w", encoding="utf-8", newline="") as f:
        wcsv = csv.writer(f)
        wcsv.writerow(["idx", "t_rel_s", "interval_ms", "cpu_ms", "frame",
                       "mode", "fg", "df", "gap", "hiccup", "win_cyc_delta",
                       "cyc_est_ms", "win_cpu_cum_ms", "win_kernel_cum_ms",
                       "win_user_cum_ms", "ctx", "note"])
        for r in rows:
            wcsv.writerow([
                r.get("idx"), round(r.get("t_rel_s") or 0, 6),
                (round(r["interval_ms"], 4) if r.get("interval_ms") is not None else None),
                (round(r["cpu_ms"], 6) if r.get("cpu_ms") is not None else None),
                r.get("frame"), r.get("mode"), r.get("fg"), r.get("df"),
                int(bool(r.get("gap"))), int(bool(r.get("hiccup"))),
                r.get("win_cyc_delta"),
                (round(r["win_cyc_delta"] / cyc_per_ms, 6)
                 if (cyc_per_ms and r.get("win_cyc_delta") is not None) else None),
                (round(r["win_cpu_cum_ms"], 6) if r.get("win_cpu_cum_ms") is not None else None),
                r.get("win_kernel_cum_ms"), r.get("win_user_cum_ms"),
                r.get("ctx"), r.get("note") or ("gap" if r.get("gap") else "")])

    analysis = {
        "meta_run": {k: meta.get(k) for k in
                     ("pid", "is32", "game_tid", "map", "phase_stop", "error",
                      "getprocesstimes_probe", "n_samples", "n_read_fail",
                      "n_winthread_fail", "started_utc", "ended_utc")},
        "segment": {"start_t_mono_ns": t0, "end_t_mono_ns": t1,
                    "wall_s": seg_wall_s,
                    "n_ok_samples": len(seg), "n_post_end_samples": len(post),
                    "fg_true": fg_true,
                    "sampling_interval": samp_int},
        "attribution_note": "每拍成本=相邻 frame 递增采样间 Δ(win_kernel+win_user)；"
                            "窗口=1拍±采样量化；含渲染+消息泵+逻辑；"
                            "CPU 时间不含阻塞等待（Sleep/Present/vsync/等消息）。",
        "df1_distribution": dist,
        "df1_histogram_1ms": histogram(cpu_vals),
        "quantum": quantum,
        "hotspots": {"rule": ">=3x median AND >=1.0ms (df=1)",
                     "median_ms": med,
                     "n_candidates": len(hot),
                     "top20": [{k: r.get(k) for k in
                                ("t_rel_s", "cpu_ms", "frame", "mode", "fg",
                                 "interval_ms", "idx")} for r in hot_top]},
        "cycle_channel": {"n": len(cyc_rows), "cyc_per_ms": cyc_per_ms,
                          "n_hot": len(cyc_hot),
                          "top20": [{k: r.get(k) for k in
                                     ("t_rel_s", "frame", "mode", "fg",
                                      "win_cyc_delta")} for r in cyc_hot[:20]],
                          "auxiliary": True},
        "trend": {"windows_10s": trend,
                  "first_third_median_ms": med_f,
                  "last_third_median_ms": med_l,
                  "ratio": (med_l / med_f) if (med_f and med_l) else None,
                  "rising_candidate": rising,
                  "rule": "末1/3窗中位 > 首1/3窗中位 × 1.2"},
        "occupancy": {"window_thread_pct_singlecore": occ_win,
                      "process": proc_detail,
                      "unit_note": "单核百分比；CPU 时间不含阻塞等待"},
        "cpu_vs_interval": {"n": len(pairs), "pearson": r_p, "spearman": r_s,
                            "note": "只描述相关，不归因"},
        "zero_input": {"watcher_scans_in_seg": len(last_inputs),
                       "distinct_last_input": len(set(last_inputs)),
                       "ok": zero_input},
        "multi_tick_events": [{"t_rel_s": r.get("t_rel_s"), "cpu_ms": r.get("cpu_ms"),
                               "df": r.get("df"), "frame": r.get("frame"),
                               "interval_ms": r.get("interval_ms"),
                               "hiccup": r.get("hiccup")} for r in dmulti],
        "gap_rows_n": len(gap_rows),
        "tier": tier,
    }
    (OUT / "analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=1, default=str),
        encoding="utf-8")
    print("written: analysis.json, tickcost.csv (%d rows)" % len(rows))
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
