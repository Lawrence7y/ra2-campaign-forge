#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W91 ANALYZE - in-trip phase split (march vs combat), CPU consumption rates.

Pre-registered (written into PROGRESS.md BEFORE the P1 run):
  A phase = samples with phase=="A"  (A8ED50==0 AND X87E8E0 changing)
  B phase = samples with phase=="B"  (after first A8ED50 nonzero)
  Primary statistic = window-thread CPU consumption rate per phase
  (Sigma win_cpu_ms_delta over consecutive sample pairs whose LATER sample is
  in the phase / Sigma wall time of those intervals, FILETIME kernel+user,
  single-core %).  Cycle channel reported alongside.
  Interval attribution: an interval belongs to the phase of its later sample
  (the 6 ms boundary interval is attributed to B; impact < one sample).

  Reference anchors (QUOTED, not re-run):
    W88 signed pair   : combat 33.6062 % vs control 18.0950 %  (ratio 1.857)
    W90 pair_c        : combat 31.0087 % vs control 17.7624 %  (ratio 1.746)
    W90 pair_d        : see out/analysis.json (ratio 1.801)
  Pre-registered verdict table (NO significance language, no p/CI):
    A in 31-33.6 band      => +75~86% 主要来自行军/寻路，不是交战
    A in 17.75-18.10 band  => 交战是驱动，行军/寻路贡献接近 0
    18.10 < A < 31.0       => 行军贡献约 (A - 17.9) 个百分点、
                              交战贡献约 (B - A) 个百分点；单趟单布局初估
  CAVEAT (also pre-registered): B phase has 200 enemy units, C6 arm has 1200;
  B vs C6 is NOT a like-for-like comparison and is reported as context only.

Usage: python w91_analyze.py trip_P1 [trip_P2 ...]
Writes out/analysis.json and prints a summary.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

W91 = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r06\W91_approach")
OUT = W91 / "out"
NS_MS = 1e9

REFS = {
    "W88_signed_pair": {"combat_pct": 33.6062, "control_pct": 18.0950,
                        "ratio": 1.857, "n_enemy": 1200},
    "W90_pair_c": {"combat_pct": 31.0087, "control_pct": 17.7624,
                   "ratio": 1.746, "n_enemy": 1200},
    "W90_pair_d": {"combat_pct": 33.6062, "control_pct": 18.0950,
                   "ratio": 1.801, "n_enemy": 1200,
                   "note": "placeholder - re-read from W90 analysis.json when "
                           "writing APPROACH.md"},
}


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


def window_rates(win):
    """FILETIME rate + cycle rate over consecutive pairs of this window."""
    if len(win) < 5:
        return None
    t0, t1 = win[0]["t_perf_ns"], win[-1]["t_perf_ns"]
    wall = (t1 - t0) / NS_MS
    if wall <= 0:
        return None
    sum_ms = 0.0
    sum_cyc = 0.0
    fs = []
    for i in range(1, len(win)):
        a, b = win[i - 1], win[i]
        if b.get("read_status") != "ok" or a.get("read_status") != "ok":
            continue
        cd, md = b.get("win_cyc_delta"), b.get("win_cpu_ms_delta")
        w = (b["t_perf_ns"] - a["t_perf_ns"]) / NS_MS
        if md is not None:
            sum_ms += md
        if cd is not None:
            sum_cyc += cd
        if cd is not None and md is not None and md > 0 and w > 0:
            fs.append(cd / (md / 1000.0))
    freq = statistics.median(fs) if fs else None
    res = {"rate_pct_filetime": round(sum_ms / wall / 10.0, 4),
           "wall_s": round(wall, 3), "n": len(win),
           "sum_cpu_ms": round(sum_ms, 2),
           "implied_freq_hz": round(freq) if freq else None,
           "implied_freq_n": len(fs)}
    if freq:
        res["rate_pct_cycle"] = round(sum_cyc / freq / wall / 10.0, 4)
    return res


def phase_rates(s):
    """Phase A / B / pre / full windows; interval attributed to its LATER
    sample's phase."""
    pre = [r for r in s if r.get("phase") == "pre"]
    a = [r for r in s if r.get("phase") == "A"]
    b = [r for r in s if r.get("phase") == "B"]
    out = {"full": window_rates(s),
           "pre": window_rates(pre) if len(pre) >= 5 else None,
           "A": window_rates(a) if len(a) >= 5 else None,
           "B": window_rates(b) if len(b) >= 5 else None}
    # x87 change count inside A (from the per-sample phase tag)
    out["A_sample_n"] = len(a)
    out["B_sample_n"] = len(b)
    out["pre_sample_n"] = len(pre)
    if a:
        out["A_start_ingame_s"] = a[0].get("elapsed_ingame_s")
        out["A_end_ingame_s"] = a[-1].get("elapsed_ingame_s")
        out["A_wall_s"] = round((a[-1]["t_perf_ns"] - a[0]["t_perf_ns"]) / NS_MS, 3)
    if b:
        out["B_start_ingame_s"] = b[0].get("elapsed_ingame_s")
        out["B_end_ingame_s"] = b[-1].get("elapsed_ingame_s")
        out["B_wall_s"] = round((b[-1]["t_perf_ns"] - b[0]["t_perf_ns"]) / NS_MS, 3)
    return out


def anchors(s):
    nz_idx = None
    x87_idx = None
    x87_first = None
    prev = None
    x87_changes = 0
    x87_changes_A = 0
    for i, r in enumerate(s):
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
            if r.get("phase") == "A":
                x87_changes_A += 1
    return {"a8ed50_first_nonzero_idx": nz_idx,
            "a8ed50_first_nonzero_t_ingame_s": (
                s[nz_idx].get("elapsed_ingame_s") if nz_idx is not None else None),
            "x87e8e0_first_value": x87_first,
            "x87e8e0_first_change_idx": x87_idx,
            "x87e8e0_first_change_t_ingame_s": (
                s[x87_idx].get("elapsed_ingame_s")
                if x87_idx is not None else None),
            "x87e8e0_n_changes": x87_changes,
            "x87e8e0_n_changes_phase_A": x87_changes_A}


def verdict(A_pct, B_pct):
    if A_pct is None:
        return "A 相位样本不足，判读不适用"
    if 31.0 <= A_pct <= 33.6:
        return ("A 相位 %.2f%% 落在 C6 交战臂带（31.0-33.6%%）⇒ "
                "+75~86%% 主要来自行军/寻路，不是交战 [预注册判读]" % A_pct)
    if 17.75 <= A_pct <= 18.10:
        return ("A 相位 %.2f%% 落在 CTRL_C6 对照带（17.75-18.10%%）⇒ "
                "交战是驱动，行军/寻路贡献接近 0 [预注册判读]" % A_pct)
    if 18.10 < A_pct < 31.0:
        march = A_pct - 17.9
        combat = (B_pct - A_pct) if B_pct is not None else None
        return ("中间带：行军贡献约 %.1f 个百分点（A=%.2f%% − 对照中值 17.9%%），"
                "交战贡献约 %s 个百分点（B−A）；单趟、单布局的初估 [预注册判读]"
                % (march, A_pct,
                   ("%.1f" % combat) if combat is not None else "n/a"))
    return ("A=%.2f%% 落在预注册三带之外（<17.75 或 >33.6），按实际值如实报告"
            % A_pct)


def trip_stats(trip):
    p = OUT / trip / "run.ndjson"
    if not p.is_file():
        return {"trip": trip, "error": "no ndjson"}
    s = samples_of(load_ndjson(p))
    if not s:
        return {"trip": trip, "error": "no samples"}
    res = {"trip": trip}
    rp = OUT / trip / "TRIP_RESULT.json"
    if rp.is_file():
        r = json.loads(rp.read_text(encoding="utf-8"))
        res["outcome"] = r.get("outcome")
        res["ok"] = r.get("ok")
        res["terminal"] = (r.get("terminal") or {}).get("kind")
        res["ingame_s"] = (r.get("sampling") or {}).get("ingame_duration_s")
        res["stop_reason"] = (r.get("sampling") or {}).get("stop_reason")
    res.update(anchors(s))
    pr = phase_rates(s)
    res["rates"] = pr
    A_pct = (pr.get("A") or {}).get("rate_pct_filetime")
    B_pct = (pr.get("B") or {}).get("rate_pct_filetime")
    res["A_pct_filetime"] = A_pct
    res["B_pct_filetime"] = B_pct
    res["verdict"] = verdict(A_pct, B_pct)
    return res


def main():
    trips = sys.argv[1:] or ["trip_P1"]
    rep = {"note": "W91 phase split; NO significance language",
           "references": REFS, "trips": {t: trip_stats(t) for t in trips}}
    out = OUT / "analysis.json"
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2, default=str),
                   encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
