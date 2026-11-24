#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W85 ANALYZE - offline recompute for the pressure/control pilot trips.

Inputs : W85_pressure/out/trip_{pressure,control}/run.ndjson
         + TRIP_RESULT_{pressure,control}.json
         + screenshots in the trip dirs.
Outputs: W85_pressure/out/analysis.json, tickcost_<arm>.csv, stdout summary.

PRE-REGISTERED (frozen before any trip, from LEAD 2026-11-14):
 * PRIMARY statistic = window-thread CPU consumption rate =
       sum(thread CPU over analysis window) / measured wall time
   = single-core occupancy.  Cycle channel converted with the trip's own
   whole-window self-calibration (cyc_per_ms = sum(dCyc)/sum(dCpuMS));
   FILETIME kernel+user channel as cross-check (15.625 ms quantum washes out
   over minutes).
 * Secondary only: per-tick CPU median/p95, per-second occupancy median/p95.
 * NO per-tick-cost / FPS interpretation of CPU or of 0xA8ED84.
 * Analysis window per arm (same rule both arms): ingame samples with
   30 s < t_ingame <= T_end, T_end = terminal t_ingame if a terminal state
   was detected else the trip's ingame duration.  Samples with read_status
   fail contribute no deltas (delta skipped if either endpoint failed).
 * Quality flags: window < 240 s => INSUFFICIENT; fg-loss samples > 5% =>
   QUALITY flag; read-fail > 0.5% => QUALITY flag.
 * Verdict (pilot wording, NO significance language):
   ratio = rate_pressure / rate_control (cycle channel; filetime shown too).
   ratio < 1.10 AND a8ed50_nz_pressure >= 3x a8ed50_nz_control (control==0
   counts as satisfied iff pressure nz > 0) =>
       「本场景、本剂量范围内未观测到与兵力成比例的负载抬升」
   ratio >= 1.10 => 初估抬升 X%，需下一轮剂量反应确认。
 * Independent load evidence: E1 A8ED50 nonzero ratio/peak/histogram;
   E2 screenshot pixel diffs (within-arm consecutive + cross-arm same mark);
   E3 B0CE88/X87E8E0 proxies; E4 actual 0xA8ED84 counts/s under load.
"""
from __future__ import annotations

import csv
import json
import math
import statistics
import sys
from pathlib import Path

W85 = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r03\W85_pressure")
OUT = W85 / "out"
ARMS = ("pressure", "control")
WARMUP_S = 30.0
MIN_VALID_S = 240.0
NZ_RATIO_FACTOR = 3.0
RATIO_LINE = 1.10


def load_ndjson(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    return rows


def pct(sorted_vals, p):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)


def analyze_arm(arm):
    rep = {"arm": arm}
    res = json.loads((OUT / ("TRIP_RESULT_%s.json" % arm)).read_text(encoding="utf-8"))
    rep["trip"] = {k: res.get(k) for k in
                   ("arm", "outcome", "ok", "pid", "installed_map_matches_arm_package")}
    sampling = res.get("sampling") or {}
    rep["trip"]["n_samples"] = sampling.get("n_samples")
    rep["trip"]["ingame_duration_s"] = sampling.get("ingame_duration_s")
    rep["trip"]["stop_reason"] = sampling.get("stop_reason")
    rep["trip"]["n_read_fail_counter"] = sampling.get("n_read_fail")
    rep["trip"]["n_fg_loss_samples"] = sampling.get("n_fg_loss_samples")

    rows = load_ndjson(OUT / ("trip_%s" % arm) / "run.ndjson")
    samples = [r for r in rows if r.get("kind") == "sample"]
    rep["n_sample_rows"] = len(samples)

    # ---- window selection ----
    term = res.get("terminal") or {}
    t_end = None
    if term.get("t_ingame_s") is not None:
        t_end = float(term["t_ingame_s"])
    ingame = [r for r in samples if r.get("elapsed_ingame_s") is not None]
    if t_end is None:
        t_end = sampling.get("ingame_duration_s") or 0.0
    win = [r for r in ingame if WARMUP_S < r["elapsed_ingame_s"] <= t_end]
    rep["window"] = {"warmup_s": WARMUP_S, "t_end_s": round(t_end, 3),
                     "n_samples_window": len(win),
                     "terminal_kind": term.get("kind"),
                     "terminal_t_ingame_s": term.get("t_ingame_s")}
    if len(win) < 2:
        rep["verdict_data"] = "NO_WINDOW"
        return rep
    t0 = win[0]["t_perf_ns"]
    t1 = win[-1]["t_perf_ns"]
    wall_s = (t1 - t0) / 1e9
    rep["window"]["wall_s"] = round(wall_s, 3)

    # ---- deltas (skip pairs where either endpoint read failed) ----
    d_cyc = []
    d_cpu_ms = []
    d_frame = []
    tick_ms = []          # per-tick cost proxy in ms (SECONDARY ONLY)
    per_sec = {}          # second bucket -> cpu_ms (cycle channel, ms)
    a8ed50_nonzero = 0
    a8ed50_peak = 0
    a8ed50_hist = {}
    b0_nonzero = 0
    b0_peak = 0
    x87_nonzero = 0
    x87_peak = 0
    n_interval_ge64 = 0
    n_df_ge2 = 0
    interval_vals = []
    fg_loss_win = 0
    n_fail_win = 0
    frame0 = win[0].get("frame")
    frame_last = frame0
    for i in range(1, len(win)):
        a, b = win[i - 1], win[i]
        iv = b.get("interval_ms_actual")
        if iv is not None:
            interval_vals.append(iv)
            if iv >= 64.0:
                n_interval_ge64 += 1
        if b.get("win_foreground") is False:
            fg_loss_win += 1
        if b.get("read_status") != "ok" or a.get("read_status") != "ok":
            n_fail_win += 1
            continue
        if b.get("win_cyc_delta") is not None:
            d_cyc.append(b["win_cyc_delta"])
        if b.get("win_cpu_ms_delta") is not None:
            d_cpu_ms.append(b["win_cpu_ms_delta"])
            sec = int(b["elapsed_ingame_s"])
            per_sec[sec] = per_sec.get(sec, 0.0) + b["win_cpu_ms_delta"]
        fb = b.get("frame")
        fa = a.get("frame")
        if fb is not None and fa is not None:
            df = fb - fa
            d_frame.append(df)
            if df >= 2:
                n_df_ge2 += 1
            frame_last = fb
        v = b.get("A8ED50") or 0
        if v:
            a8ed50_nonzero += 1
            a8ed50_peak = max(a8ed50_peak, v)
            a8ed50_hist[v] = a8ed50_hist.get(v, 0) + 1
        v = b.get("B0CE88") or 0
        if v:
            b0_nonzero += 1
            b0_peak = max(b0_peak, v)
        v = b.get("X87E8E0") or 0
        if v:
            x87_nonzero += 1
            x87_peak = max(x87_peak, v)
    n_win = len(win)
    rep["window"]["n_fg_loss"] = fg_loss_win
    rep["window"]["n_read_fail_pairs"] = n_fail_win

    sum_cyc = sum(d_cyc)
    sum_cpu_ms = sum(d_cpu_ms)
    cyc_per_ms = (sum_cyc / sum_cpu_ms) if sum_cpu_ms > 0 else None
    rate_cyc = (sum_cyc / cyc_per_ms / wall_s) if cyc_per_ms else None
    rate_ft = sum_cpu_ms / wall_s if wall_s > 0 else None
    for v in d_cyc:
        if cyc_per_ms:
            tick_ms.append(v / cyc_per_ms)
    tick_sorted = sorted(tick_ms)
    occ_sorted = sorted(v for v in per_sec.values())
    df_sorted = sorted(d_frame)
    frame_delta_total = sum(d_frame)
    rep["calibration"] = {
        "sum_cycle": int(sum_cyc), "sum_cpu_ms_filetime": round(sum_cpu_ms, 3),
        "cyc_per_ms_selfcalibrated": (round(cyc_per_ms, 1) if cyc_per_ms else None)}
    rep["primary_rate"] = {
        "channel": "window-thread CPU / wall time (single-core occupancy)",
        "rate_cycle_ms_per_s": (round(rate_cyc, 4) if rate_cyc else None),
        "rate_cycle_pct_singlecore": (round(rate_cyc * 100.0, 4) if rate_cyc else None),
        "rate_filetime_ms_per_s": (round(rate_ft, 4) if rate_ft else None),
        "rate_filetime_pct_singlecore": (round(rate_ft * 100.0, 4) if rate_ft else None),
        "note": "PRIMARY per pre-registration; NOT per-tick cost, NOT FPS"}
    rep["secondary"] = {
        "tick_ms_median": (round(pct(tick_sorted, 50), 4) if tick_sorted else None),
        "tick_ms_p95": (round(pct(tick_sorted, 95), 4) if tick_sorted else None),
        "tick_ms_p99": (round(pct(tick_sorted, 99), 4) if tick_sorted else None),
        "persec_occupancy_median_pct": (round(pct(occ_sorted, 50) / 10.0, 4)
                                        if occ_sorted else None),
        "persec_occupancy_p95_pct": (round(pct(occ_sorted, 95) / 10.0, 4)
                                     if occ_sorted else None),
        "note": "persec buckets are 1 s CPU ms / 10 ms = single-core %"},
    rep["cadence"] = {
        "interval_ms_median": (round(pct(sorted(interval_vals), 50), 3)
                               if interval_vals else None),
        "interval_ms_p99": (round(pct(sorted(interval_vals), 99), 3)
                            if interval_vals else None),
        "n_interval_ge64ms": n_interval_ge64,
        "n_df_ge2_multitick_jumps": n_df_ge2,
        "df_histogram_top": {str(k): df_sorted.count(k)
                             for k in sorted(set(d_frame))[:8]},
        "frame_first": frame0, "frame_last": frame_last,
        "frame_rate_counts_per_s": (round(frame_delta_total / wall_s, 4)
                                    if wall_s > 0 else None),
        "note": "E4: actual 0xA8ED84 counter rate under load; timer, not FPS"}
    rep["evidence_e1_a8ed50"] = {
        "n_window": n_win, "nonzero_n": a8ed50_nonzero,
        "nonzero_ratio": (round(a8ed50_nonzero / n_win, 6) if n_win else None),
        "peak": a8ed50_peak,
        "hist_top10": dict(sorted(a8ed50_hist.items(),
                                  key=lambda kv: -kv[1])[:10])}
    rep["evidence_e3_proxies"] = {
        "B0CE88_nonzero_n": b0_nonzero, "B0CE88_peak": b0_peak,
        "X87E8E0_nonzero_n": x87_nonzero, "X87E8E0_peak": x87_peak}
    rep["quality"] = {
        "window_s": round(t_end - WARMUP_S, 3),
        "min_valid_met": (t_end - WARMUP_S) >= MIN_VALID_S,
        "fg_loss_ratio": (round(fg_loss_win / n_win, 5) if n_win else None),
        "read_fail_ratio": (round(n_fail_win / n_win, 5) if n_win else None)}
    rep["a8ed50_nz_ratio"] = rep["evidence_e1_a8ed50"]["nonzero_ratio"]

    # ---- tickcost csv (per-tick, secondary channel) ----
    csvp = OUT / ("tickcost_%s.csv" % arm)
    with csvp.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_ingame_s", "interval_ms", "frame", "cyc_delta",
                    "cpu_ms_delta_filetime", "tick_ms_cyc", "A8ED50",
                    "B0CE88", "X87E8E0", "win_foreground", "read_status"])
        for i in range(1, len(win)):
            a, b = win[i - 1], win[i]
            cd = b.get("win_cyc_delta")
            tick = (round(cd / cyc_per_ms, 4)
                    if (cd is not None and cyc_per_ms) else None)
            w.writerow([b.get("elapsed_ingame_s"),
                        b.get("interval_ms_actual"), b.get("frame"),
                        cd, b.get("win_cpu_ms_delta"), tick,
                        b.get("A8ED50"), b.get("B0CE88"), b.get("X87E8E0"),
                        b.get("win_foreground"), b.get("read_status")])
    rep["tickcost_csv"] = str(csvp)
    return rep


def screenshot_diffs():
    """E2: within-arm consecutive pixel diffs + cross-arm same-mark diffs."""
    from PIL import Image, ImageChops
    rep = {}

    def stats(p1, p2):
        try:
            i1 = Image.open(p1).convert("L")
            i2 = Image.open(p2).convert("L")
            if i1.size != i2.size:
                i2 = i2.resize(i1.size)
            d = ImageChops.difference(i1, i2)
            h = d.histogram()
            n = sum(h)
            changed = sum(h[8:])            # pixels with diff >= 8
            mean = sum(v * c for v, c in enumerate(h)) / max(n, 1)
            return {"pixels_changed_ge8_pct": round(100.0 * changed / max(n, 1), 3),
                    "mean_abs_diff": round(mean, 3)}
        except Exception as e:
            return {"error": repr(e)}

    marks = ["combat_t%03d" % m for m in (30, 90, 150, 210, 270)
             if m <= 300]
    for arm in ARMS:
        d = OUT / ("trip_%s" % arm)
        rows = []
        prev = None
        for m in marks:
            p = d / ("screen_run_%s_%s.png" % (arm, m))
            if not p.is_file():
                continue
            if prev is not None:
                rows.append({"pair": [prev[0], m], **stats(prev[1], str(p))})
            prev = (m, str(p))
        rep["within_%s" % arm] = rows
    # cross-arm at the same mark
    cross = []
    for m in marks:
        p1 = OUT / ("trip_pressure") / ("screen_run_pressure_%s.png" % m)
        p2 = OUT / ("trip_control") / ("screen_run_control_%s.png" % m)
        if p1.is_file() and p2.is_file():
            cross.append({"mark": m, **stats(str(p1), str(p2))})
    rep["cross_arm_same_mark"] = cross
    rep["note"] = ("E2: pressure within-arm diffs should be large (units move/"
                   "explode); control within-arm should be small; cross-arm "
                   "large (engagement visible). Evidence only, no numbers read "
                   "from pixels per red line #7.")
    return rep


def main():
    reps = {arm: analyze_arm(arm) for arm in ARMS}
    try:
        shots = screenshot_diffs()
    except Exception as e:
        shots = {"error": repr(e)}

    verdict = {"rule": "pilot pre-registered (no significance language)"}
    rp, rc = reps.get("pressure", {}).get("primary_rate"), \
        reps.get("control", {}).get("primary_rate")
    if rp and rc and rp.get("rate_cycle_pct_singlecore") and \
            rc.get("rate_cycle_pct_singlecore"):
        ratio = rp["rate_cycle_pct_singlecore"] / rc["rate_cycle_pct_singlecore"]
        verdict["rate_ratio_cycle"] = round(ratio, 4)
        verdict["rate_pct_pressure"] = rp["rate_cycle_pct_singlecore"]
        verdict["rate_pct_control"] = rc["rate_cycle_pct_singlecore"]
    if rp and rc and rp.get("rate_filetime_pct_singlecore") and \
            rc.get("rate_filetime_pct_singlecore"):
        verdict["rate_ratio_filetime"] = round(
            rp["rate_filetime_pct_singlecore"] / rc["rate_filetime_pct_singlecore"], 4)
    nzp = reps.get("pressure", {}).get("a8ed50_nz_ratio")
    nzc = reps.get("control", {}).get("a8ed50_nz_ratio")
    if nzp is not None and nzc is not None:
        verdict["a8ed50_nz_ratio_pressure"] = nzp
        verdict["a8ed50_nz_ratio_control"] = nzc
        combat_heavier = (nzp >= NZ_RATIO_FACTOR * nzc) if nzc > 0 else (nzp > 0)
        verdict["combat_evidently_heavier"] = bool(combat_heavier)
    if "rate_ratio_cycle" in verdict and "combat_evidently_heavier" in verdict:
        if verdict["rate_ratio_cycle"] < RATIO_LINE:
            verdict["conclusion"] = ("本场景、本剂量范围内未观测到与兵力成比例的"
                                     "负载抬升（试点；比值 %.3f < 1.10）"
                                     % verdict["rate_ratio_cycle"])
        else:
            verdict["conclusion"] = ("初估抬升 %.1f%%，需下一轮剂量反应确认"
                                     % ((verdict["rate_ratio_cycle"] - 1.0) * 100.0))
    else:
        verdict["conclusion"] = "数据不足以给出预注册判读（见 analysis.json quality）"

    out = {"arms": reps, "screenshots_e2": shots, "verdict_pilot": verdict,
           "pre_registered": {"warmup_s": WARMUP_S, "min_valid_s": MIN_VALID_S,
                              "ratio_line": RATIO_LINE,
                              "nz_factor": NZ_RATIO_FACTOR}}
    (OUT / "analysis.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"verdict": verdict,
                      "pressure": {k: reps["pressure"].get(k)
                                   for k in ("primary_rate", "quality",
                                             "evidence_e1_a8ed50", "cadence")
                                   if k in reps["pressure"]},
                      "control": {k: reps["control"].get(k)
                                  for k in ("primary_rate", "quality",
                                            "evidence_e1_a8ed50", "cadence")
                                  if k in reps["control"]}},
                     ensure_ascii=False, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
