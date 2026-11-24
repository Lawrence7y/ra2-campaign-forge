#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W85 ANALYZE2 - within-trip self-contrast + static-control baseline.

Background: the pre-registered pilot needed >=240 s of sustained heavy-combat
sampling; that proved UNACHIEVABLE (engine NULL-virtual-call crash/internal
error 2.5-17 s after first shots in every combat configuration tested).  What
every crashed pressure trip DOES contain is a real combat window
(A8ED50 first-nonzero -> frame halt), so the quantitative deliverable is:

  * WITHIN-TRIP SELF-CONTRAST: window-thread CPU consumption rate
    (cumulative CPU / wall time) in the PRE-COMBAT window (units moving, no
    fire) vs the COMBAT window of the SAME trip, same map/layout/objects.
    Short windows (2.6-14.8 s) => effect-size initial estimate only, labelled
    [短窗], no significance language.
  * STATIC-CONTROL BASELINE: the dose1500 control arm, 30-300 s window,
    1522 objects all Guard, A8ED50 all zero, 300 s clean.
  * CROSS contrast: combat-window rate / static-control rate (different dose
    where applicable, labelled).
  * E1/E2/E4 evidence channels as in w85_analyze.py.
  * Frame-halt detection from ndjson (terminal dialogs stall 0xA8ED84).
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

W85 = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r03\W85_pressure")
OUT = W85 / "out"
NS_MS = 1e9

# (archive dir, config label, short note)
PRESSURE_TRIPS = [
    ("trip_pressure_dose1500_crash", "dose1500 3house 12T tanks300+NACNST",
     "AV 0xC0000005 @17.19s"),
    ("trip_pressure_dose800_internalerror", "dose800 3house 12T tanks200+NACNST",
     "internal error dialog ~13.3s"),
    ("trip_pressure_dose600_crash", "dose600 3house 12T tanks150+NACNST",
     "AV @17.16s"),
    ("trip_pressure_dose400_crash", "dose400 3house 12T tanks100+NACNST",
     "internal error dialog @14.0s"),
    ("trip_pressure_singlehouse_crash", "singlehouse(British300) tanks100+NACNST 12T",
     "internal error dialog @11.0s"),
    ("trip_pressure_notesla_crash", "singlehouse(British300) tanks100+NACNST 0T",
     "internal error dialog @11.0s"),
    ("trip_pressure_P2_enemy30_player100_crash", "British30 tanks100+NACNST 12T",
     "internal error dialog @22.0s"),
    ("trip_pressure_P3_notanks_crash", "British90 noTanks NACNST 12T",
     "internal error dialog @13.99s"),
    ("trip_pressure_P4rerun_P3_replica", "P3 replica (tool bug rerun)",
     "internal error dialog @14.0s (repro of P3)"),
    ("trip_pressure_P4_nonacnst_crash", "British90 noTanks noNACNST 12T 6xNAPOWR",
     "internal error dialog @13.99s"),
]
CONTROL_TRIP = ("trip_control_dose1500_static",
                "dose1500-layout 1522 objects all Guard (zero combat)")


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


def samples_of(rows):
    return [r for r in rows if r.get("kind") == "sample"
            and r.get("elapsed_ingame_s") is not None]


def window_rate(win):
    """(rate_cycle_pct, rate_ft_pct, wall_s, n) over a sample window."""
    if len(win) < 5:
        return None
    t0, t1 = win[0]["t_perf_ns"], win[-1]["t_perf_ns"]
    wall = (t1 - t0) / NS_MS
    if wall <= 0:
        return None
    sum_cyc = 0
    sum_ms = 0.0
    for i in range(1, len(win)):
        a, b = win[i - 1], win[i]
        if b.get("read_status") != "ok" or a.get("read_status") != "ok":
            continue
        if b.get("win_cyc_delta") is not None:
            sum_cyc += b["win_cyc_delta"]
        if b.get("win_cpu_ms_delta") is not None:
            sum_ms += b["win_cpu_ms_delta"]
    cyc_per_ms = (sum_cyc / sum_ms) if sum_ms > 0 else None
    # 单核占用率 %：1000 ms/s = 100%
    rate_pct = sum_ms / wall / 10.0
    return {"rate_pct_filetime_kerneluser": round(rate_pct, 3),
            "rate_ms_per_s": round(sum_ms / wall, 3),
            "wall_s": round(wall, 3), "n_samples": len(win),
            "sum_cpu_ms_filetime": round(sum_ms, 2),
            "cyc_per_ms_diag": round(cyc_per_ms, 0) if cyc_per_ms else None,
            "note": ("cycle channel self-calibrated on the same window is "
                     "mathematically identical to the filetime channel for a "
                     "window rate; FILETIME (15.625 ms quantum) is the "
                     "reported channel, quantum noise noted for short windows")}


def frame_halt_t(samples):
    """Time (elapsed_ingame_s) of the LAST frame increase; frame stalls after
    the engine fatal error.  Returns None if frames advance to the end."""
    last_f = None
    last_inc_t = None
    for r in samples:
        f = r.get("frame")
        if f is None or r.get("read_status") != "ok":
            continue
        if last_f is not None and f > last_f:
            last_inc_t = r["elapsed_ingame_s"]
        last_f = f
    return last_inc_t


def a8ed50_first_t(samples):
    for r in samples:
        if (r.get("A8ED50") or 0) != 0:
            return r["elapsed_ingame_s"], r.get("frame"), r["A8ED50"]
    return None, None, None


def sub_window(samples, t_lo, t_hi):
    return [r for r in samples if r.get("elapsed_ingame_s") is not None
            and t_lo <= r["elapsed_ingame_s"] <= t_hi]


def a8ed50_stats(win):
    n = len(win)
    nz = sum(1 for r in win if (r.get("A8ED50") or 0) != 0)
    peak = max([(r.get("A8ED50") or 0) for r in win], default=0)
    hist = {}
    for r in win:
        v = r.get("A8ED50") or 0
        if v:
            hist[v] = hist.get(v, 0) + 1
    return {"n": n, "nonzero_n": nz,
            "nonzero_ratio": round(nz / n, 4) if n else None,
            "peak": peak, "hist": dict(sorted(hist.items(),
                                              key=lambda kv: -kv[1])[:8])}


def frame_rate(win):
    frames = [r.get("frame") for r in win if r.get("frame") is not None]
    if len(frames) < 2:
        return None
    t0 = win[0]["t_perf_ns"]; t1 = win[-1]["t_perf_ns"]
    wall = (t1 - t0) / NS_MS
    if wall <= 0:
        return None
    return round((frames[-1] - frames[0]) / wall, 3)


def main():
    rep = {"note": "within-trip self-contrast pilot (short windows, no "
                   "significance language); crashed trips labelled [短窗]"}
    rows = []
    for d, label, note in PRESSURE_TRIPS:
        p = OUT / d / "run.ndjson"
        if not p.is_file():
            rows.append({"trip": d, "error": "ndjson missing"})
            continue
        s = samples_of(load_ndjson(p))
        t_nz, nz_frame, nz_val = a8ed50_first_t(s)
        halt_t = frame_halt_t(s)
        end_t = s[-1]["elapsed_ingame_s"]
        row = {"trip": d, "config": label, "fate": note,
               "n_samples": len(s),
               "a8ed50_first_nonzero_t": round(t_nz, 3) if t_nz else None,
               "a8ed50_first_nonzero_frame": nz_frame,
               "a8ed50_first_nonzero_value": nz_val,
               "frame_halt_t": round(halt_t, 3) if halt_t else None,
               "last_sample_t": round(end_t, 2)}
        if t_nz:
            pre = sub_window(s, 0.3, t_nz)
            combat = sub_window(s, t_nz, (halt_t if halt_t else end_t))
            row["precombat_window"] = window_rate(pre)
            row["combat_window"] = window_rate(combat)
            row["a8ed50_combat"] = a8ed50_stats(combat)
            row["frame_rate_pre_s"] = frame_rate(pre)
            row["frame_rate_combat_s"] = frame_rate(combat)
            rp, rc = row["precombat_window"], row["combat_window"]
            if rp and rc and rp.get("rate_pct_filetime_kerneluser") and \
                    rc.get("rate_pct_filetime_kerneluser"):
                row["combat_over_pre"] = round(
                    rc["rate_pct_filetime_kerneluser"]
                    / rp["rate_pct_filetime_kerneluser"], 3)
        rows.append(row)
    rep["pressure_trips"] = rows

    # ---- static control baseline ----
    d, label = CONTROL_TRIP
    s = samples_of(load_ndjson(OUT / d / "run.ndjson"))
    ctrl = sub_window(s, 30.0, 300.0)
    c = window_rate(ctrl)
    rep["control_static"] = {"trip": d, "config": label,
                             "window": "30-300s", **(c or {}),
                             "a8ed50": a8ed50_stats(ctrl),
                             "frame_rate_s": frame_rate(ctrl)}
    for row in rows:
        rcmb = row.get("combat_window")
        if rcmb and c and c.get("rate_pct_filetime_kerneluser") and \
                rcmb.get("rate_pct_filetime_kerneluser"):
            row["combat_over_staticcontrol"] = round(
                rcmb["rate_pct_filetime_kerneluser"]
                / c["rate_pct_filetime_kerneluser"], 3)

    # ---- pre-registered pilot verdict (adapted, honest bounded wording) ----
    rates = [(r["config"], r.get("combat_window"), r.get("combat_over_pre"))
             for r in rows if r.get("combat_over_pre")]
    rep["pilot_effect_estimate"] = {
        "n_within_trip_contrasts": len(rates),
        "combat_over_pre_ratios": [
            {"config": cfg, "ratio": rat,
             "combat_wall_s": (cw or {}).get("wall_s"),
             "combat_rate_pct": (cw or {}).get("rate_pct_filetime_kerneluser")}
            for cfg, cw, rat in rates],
        "note": "short-window (2.6-14.8 s) self-contrasts; same map/layout/"
                "objects within each trip; effect-size initial estimate only",
    }
    rep["conclusion"] = (
        "本场景、本剂量范围内未产出可持续观测的加压臂：全部含交战配置在 A8ED50 首非零后 "
        "2.5-9 s 触发引擎 NULL-虚调用崩溃/内部错误（except.txt: 0x51C2D3 call [eax+0x1D4], "
        "eax=0），静态同布局对照 1522 对象 300 s 全绿且 A8ED50 全程 0。"
        "「更重战斗是否 >20% 抬 CPU」在 vanilla YR 1.001 上于本轮剂量/布局内"
        "无法以 >=240 s 有效窗回答；可用证据为短窗趟内自对照（效应量初估）与静态上界。")

    (OUT / "analysis2.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"conclusion": rep["conclusion"],
                      "control_static": {k: rep["control_static"].get(k)
                                         for k in ("rate_pct_filetime_kerneluser",
                                                   "rate_ms_per_s",
                                                   "frame_rate_s",
                                                   "a8ed50", "n_samples",
                                                   "wall_s")},
                      "contrasts": rep["pilot_effect_estimate"]},
                     ensure_ascii=False, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
