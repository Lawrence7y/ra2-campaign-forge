#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W90 ANALYZE - replicate pair stats + N=3 table + render-channel stats.

Pre-registered wording (inherited from W88, frozen before any CTRL trip ran):
  Primary statistic = window-thread CPU consumption rate (Sigma GetThreadTimes
  kernel+user / wall time, single-core occupancy %).  Paired window =
  elapsed_ingame [0, min(T_end_combat, T_end_ctrl)] on BOTH trips identically.
  ratio < 1.10  => 「本配置下未观测到与交战成比例的负载抬升」
  ratio >= 1.10 => 「初估抬升 X%」
  NO significance language (no 显著/p值/CI).

Channels: FILETIME (win_cpu_ms_delta) is primary; cycle channel
(QueryThreadCycleTime, win_cyc_delta) is computed independently and reported
alongside (rate expressed via the median implied thread-cycle frequency
measured on the same samples; ratio must agree bit-wise in ordering).
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

W90 = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r05\W90_replicates")
OUT = W90 / "out"
NS_MS = 1e9

TRIP_DIRS = ["trip_C6_c", "trip_C6_d", "trip_CTRL_C6_c", "trip_CTRL_C6_d"]

# W88 signed numbers (W88_envelope/out/analysis.json, ENVELOPE.md §6) --
# listed verbatim for the N=3 table; NOT recomputed here.
W88_PAIR = {"combat_trip": "W88/trip_C6", "control_trip": "W88/trip_CTRL_C6",
            "window_s": 150.002,
            "combat_rate_pct": 33.6062, "control_rate_pct": 18.0950,
            "ratio": 1.857,
            "combat_a8ed50_nonzero_ratio": 0.9405,
            "control_a8ed50_nonzero_ratio": 0.0,
            "combat_x87e8e0_changes": 6518, "control_x87e8e0_changes": 0}


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


def implied_freqs(win):
    """Median implied thread-cycle frequency (cycles per second) from sample
    pairs with both channels healthy and cpu delta > 0."""
    fs = []
    for i in range(1, len(win)):
        a, b = win[i - 1], win[i]
        if b.get("read_status") != "ok" or a.get("read_status") != "ok":
            continue
        cd, md = b.get("win_cyc_delta"), b.get("win_cpu_ms_delta")
        if cd is None or md is None or md <= 0:
            continue
        wall_ms = (b["t_perf_ns"] - a["t_perf_ns"]) / 1e6
        if wall_ms <= 0:
            continue
        fs.append(cd / (md / 1000.0))
    return (statistics.median(fs), len(fs)) if fs else (None, 0)


def window_rates(win):
    """FILETIME channel rate + cycle channel rate over the sample window."""
    if len(win) < 5:
        return None
    t0, t1 = win[0]["t_perf_ns"], win[-1]["t_perf_ns"]
    wall = (t1 - t0) / NS_MS
    if wall <= 0:
        return None
    sum_ms = 0.0
    for i in range(1, len(win)):
        a, b = win[i - 1], win[i]
        if b.get("read_status") != "ok" or a.get("read_status") != "ok":
            continue
        if b.get("win_cpu_ms_delta") is not None:
            sum_ms += b["win_cpu_ms_delta"]
    freq, n_f = implied_freqs(win)
    res = {"rate_pct_filetime": round(sum_ms / wall / 10.0, 4),
           "wall_s": round(wall, 3), "n": len(win),
           "sum_cpu_ms": round(sum_ms, 2),
           "implied_freq_hz": round(freq) if freq else None,
           "implied_freq_n": n_f}
    if freq:
        sum_cyc = sum(b["win_cyc_delta"] for i, b in enumerate(win[1:], 1)
                      if win[i - 1].get("read_status") == "ok"
                      and b.get("read_status") == "ok"
                      and b.get("win_cyc_delta") is not None)
        res["sum_cycles"] = sum_cyc
        res["rate_pct_cycle"] = round(sum_cyc / freq / wall / 10.0, 4)
    return res


def anchors(samples):
    nz_idx = None
    x87_first = None
    x87_idx = None
    x87_changes = 0
    prev = None
    for i, r in enumerate(samples):
        if r.get("read_status") != "ok":
            continue
        if nz_idx is None and (r.get("A8ED50") or 0) != 0:
            nz_idx = i
        xv = r.get("X87E8E0")
        if x87_first is None:
            x87_first = xv
            prev = xv
        elif xv != prev:
            x87_changes += 1
            if x87_idx is None:
                x87_idx = i
            prev = xv
    return {"a8ed50_first_nonzero_idx": nz_idx,
            "x87e8e0_first_value": x87_first,
            "x87e8e0_first_change_idx": x87_idx,
            "x87e8e0_n_changes": x87_changes}


def trip_stats(d):
    p = OUT / d / "run.ndjson"
    if not p.is_file():
        return {"trip": d, "error": "no ndjson"}
    s = samples_of(load_ndjson(p))
    if not s:
        return {"trip": d, "error": "no samples"}
    res = {}
    rp = OUT / d / "TRIP_RESULT.json"
    if rp.is_file():
        r = json.loads(rp.read_text(encoding="utf-8"))
        res["outcome"] = r.get("outcome")
        res["ok"] = r.get("ok")
        res["terminal"] = (r.get("terminal") or {}).get("kind")
        res["ingame_s"] = (r.get("sampling") or {}).get("ingame_duration_s")
    res["full_window"] = window_rates(s)
    n = len(s)
    nzn = sum(1 for r in s if (r.get("A8ED50") or 0) != 0
              and r.get("read_status") == "ok")
    res["a8ed50_nonzero_ratio_full"] = round(nzn / n, 5) if n else None
    res["a8ed50_nz_n"] = nzn
    res["a8ed50_n"] = n
    res.update(anchors(s))
    res["trip"] = d
    return res


def pair(c6_dir, ctl_dir):
    c6 = trip_stats(c6_dir)
    ctl = trip_stats(ctl_dir)
    p = {"combat": {"trip": c6_dir, "T_end": c6.get("ingame_s")},
         "control": {"trip": ctl_dir, "T_end": ctl.get("ingame_s")}}
    if c6.get("ingame_s") and ctl.get("ingame_s"):
        tend = min(c6["ingame_s"], ctl["ingame_s"])
        s6 = samples_of(load_ndjson(OUT / c6_dir / "run.ndjson"))
        sc = samples_of(load_ndjson(OUT / ctl_dir / "run.ndjson"))
        w6 = window_rates([r for r in s6 if r["elapsed_ingame_s"] <= tend])
        wc = window_rates([r for r in sc if r["elapsed_ingame_s"] <= tend])
        nz6 = sum(1 for r in s6 if r["elapsed_ingame_s"] <= tend
                  and (r.get("A8ED50") or 0) != 0 and r.get("read_status") == "ok")
        n6ok = sum(1 for r in s6 if r["elapsed_ingame_s"] <= tend
                   and r.get("read_status") == "ok")
        nzc = sum(1 for r in sc if r["elapsed_ingame_s"] <= tend
                  and (r.get("A8ED50") or 0) != 0 and r.get("read_status") == "ok")
        ncok = sum(1 for r in sc if r["elapsed_ingame_s"] <= tend
                   and r.get("read_status") == "ok")
        p["window_s"] = round(tend, 3)
        p["combat"] = {"trip": c6_dir, "rates": w6,
                       "a8ed50_nonzero_ratio": round(nz6 / max(1, n6ok), 5)}
        p["control"] = {"trip": ctl_dir, "rates": wc,
                        "a8ed50_nonzero_ratio": round(nzc / max(1, ncok), 5)}
        rf = (w6["rate_pct_filetime"] / wc["rate_pct_filetime"]) \
            if (w6 and wc and wc["rate_pct_filetime"]) else None
        rc = (w6.get("rate_pct_cycle") / wc.get("rate_pct_cycle")) \
            if (w6 and wc and w6.get("rate_pct_cycle")
                and wc.get("rate_pct_cycle")) else None
        p["ratio_filetime"] = round(rf, 4) if rf else None
        p["ratio_cycle"] = round(rc, 4) if rc else None
        if rf is not None:
            if rf < 1.10:
                p["verdict"] = ("本配置下未观测到与交战成比例的负载抬升"
                                "（比值 %.3f < 1.10）" % rf)
            else:
                p["verdict"] = "初估抬升 %.1f%%（比值 %.3f）" % (
                    (rf - 1) * 100, rf)
    return p


def render_stats():
    d = OUT / "trip_C6_c" / "render_channel"
    res = {"dir": str(d), "wording": "限帧放行间隔（cnc-ddraw 限帧层），"
           "非显示帧时间、非 FPS；不得据此描述画面流畅/卡顿"}
    csvs = sorted(d.glob("framebeat_*.csv")) if d.is_dir() else []
    if not csvs:
        res["status"] = "no_csv"
        return res
    csv = csvs[0]
    res["csv"] = str(csv)
    ts = []
    with csv.open("r", encoding="ascii") as f:
        header = f.readline()
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                try:
                    ts.append(int(parts[0]))
                except ValueError:
                    pass
    if len(ts) < 3:
        res["status"] = "too_few_frames"
        res["n_frames"] = len(ts)
        return res
    ivs = [ts[i + 1] - ts[i] for i in range(len(ts) - 1)]
    srt = sorted(ivs)
    n = len(ivs)
    window_s = (ts[-1] - ts[0]) / 1000.0
    res.update({"status": "ok", "n_frames": len(ts), "n_intervals": n,
                "window_s_effective": round(window_s, 3),
                "median_ms": statistics.median(ivs),
                "p95_ms": srt[int(math.ceil(0.95 * n)) - 1],
                "p99_ms": srt[int(math.ceil(0.99 * n)) - 1],
                "max_ms": srt[-1], "min_ms": srt[0],
                "over50ms_count": sum(1 for x in ivs if x > 50),
                "over50ms_per_min": round(sum(1 for x in ivs if x > 50)
                                          / max(window_s, 1e-9) * 60.0, 3)})
    cons = d / "framebeat_console.log"
    if cons.is_file():
        res["console_tail"] = cons.read_text(encoding="utf-8",
                                             errors="replace")[-1200:]
    return res


def main():
    rep = {"note": "W90 replicate pairs; N=3 table includes the W88 signed "
                   "pair verbatim; NO significance language",
           "trips": {d: trip_stats(d) for d in TRIP_DIRS},
           "pairs": {"pair_c": pair("trip_C6_c", "trip_CTRL_C6_c"),
                     "pair_d": pair("trip_C6_d", "trip_CTRL_C6_d")},
           "w88_signed_pair": W88_PAIR,
           "render_channel_trip_C6_c": render_stats()}
    out = OUT / "analysis.json"
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2, default=str),
                   encoding="utf-8")
    print(json.dumps({"pairs": rep["pairs"], "render": rep["render_channel_trip_C6_c"]},
                     ensure_ascii=False, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
