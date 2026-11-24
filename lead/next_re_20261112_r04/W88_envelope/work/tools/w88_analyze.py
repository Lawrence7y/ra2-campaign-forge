#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W88 ANALYZE - k/N matrix + pre-registered paired-control comparison.

PRE-REGISTERED (frozen before CTRL_C6 ran, in PROGRESS.md and w88_run.py):
  Primary statistic = window-thread CPU consumption rate
  (Sigma GetThreadTimes kernel+user / wall time, single-core occupancy %).
  Window = elapsed_ingame [0, min(T_end_combat, T_end_ctrl)] applied to BOTH
  trips identically.  Also 0xA8ED50 nonzero-tick ratio in the same window.
  Verdict wording (no significance language):
    ratio < 1.10  => 「本配置下未观测到与交战成比例的负载抬升」
    ratio >= 1.10 => 「初估抬升 X%」
Mechanical anchors (Lead requirement): first A8ED50-nonzero sample idx and
first X87E8E0-change idx; "开火后 X 秒" wording is FORBIDDEN.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

W88 = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r04\W88_envelope")
OUT = W88 / "out"
NS_MS = 1e9

# (trip dir, config label, note) -- one row per RUN, dirs are unique.
TRIPS = [
    ("trip_B0", "B0 W84-df-replica 30Hunt 1TESLA 60x60 (defeat arm)",
     "defeat_dialog@9s; D2v1 mislabel ok=true, corrected in report"),
    ("trip_B1", "B1 B0+6NAPOWR(step3) (defeat arm)",
     "defeat_dialog@31s; D2v1 mislabel, corrected"),
    ("trip_C0", "C0 green-baseline rerun (all Guard)", "green"),
    ("trip_C1", "C1 MIXED DIR (pre-fix): run a @14:01 CRASH @55s (D1 "
     "artifacts: archived_except.txt/wer/ndjson-tail) + run b @14:16 green "
     "(run.ndjson/TRIP_RESULT overwritten on top)",
     "run a = crash (k counts), run b = green"),
    ("trip_C1_b", "C1 BLOCKED (stale install check, no game run)",
     "not counted"),
    ("trip_C1_c", "C1c(3rd real run) 30Hunt overlap+crewed", "green"),
    ("trip_C3", "C3a 30Hunt no-overlap", "green"),
    ("trip_C3_b", "C3b 30Hunt no-overlap (clean dir)", "green"),
    ("trip_C3_c", "C3c BLOCKED nav-timeout (no game enter)", "not counted"),
    ("trip_C3_d", "C3c(3rd real run) 30Hunt no-overlap (clean dir)", "green"),
    ("trip_C4", "C4a 30Hunt overlap+crew=no", "green"),
    ("trip_C4_b", "C4b 30Hunt overlap+crew=no", "green"),
    ("trip_C4_c", "C4c 30Hunt overlap+crew=no", "green"),
    ("trip_C6", "C6a 1200Hunt no-overlap", "green"),
    ("trip_CTRL_C6", "CTRL_C6 C6-layout all Guard", "green, A8ED50 all 0"),
    ("trip_C7", "C7 1200Hunt overlap+crew=no", "CRASH internal error @12s"),
]

KN = {  # pre-registered N=3 arms.  Evidence quality per run is UNEVEN because
       # of the D5 dir-reuse accident (see UNKNOWNS.md): runs a/b of some arms
       # lost their ndjson but survive as out-level TRIP_RESULT_<STEP>.json +
       # TAG-suffixed screenshots + (for crashes) D1 artifacts.
    "C1": {"dirs": ("trip_C1", "trip_C1_c"), "manual_crash_runs": 1,
           "note": "run a=CRASH@55s (D1 artifacts in trip_C1); run b=green "
                   "(out TRIP_RESULT_C1.json, ndjson overwritten by run c); "
                   "run c=green (trip_C1 ndjson 14:27 + out TRIP_RESULT_C1_b.json)"},
    "C3": {"dirs": ("trip_C3", "trip_C3_b", "trip_C3_d"), "manual_crash_runs": 0,
           "note": "run a=green (out TRIP_RESULT_C3.json, ndjson lost in D5 "
                   "accident); runs b/d=green (clean unique dirs, full "
                   "ndjson); trip_C3_c=BLOCKED nav-timeout, not counted"},
    "C4": {"dirs": ("trip_C4", "trip_C4_b", "trip_C4_c"), "manual_crash_runs": 1,
           "note": "run a=green (out TRIP_RESULT_C4.json, ndjson lost); run "
                   "b=CRASH@55s (trip_C4_b clean dir, full ndjson + D1); run "
                   "c=green (trip_C4_c clean dir).  Old-broken-suffix run "
                   "inside trip_C4 was green too"},
}
SINGLE = {"C0": "trip_C0", "C6": "trip_C6", "CTRL_C6": "trip_CTRL_C6",
          "C7": "trip_C7"}


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
    return {"rate_pct": round(sum_ms / wall / 10.0, 4),
            "rate_ms_per_s": round(sum_ms / wall, 3),
            "wall_s": round(wall, 3), "n": len(win),
            "sum_cpu_ms": round(sum_ms, 2)}


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
    full = window_rate(s)
    res["full_window"] = full
    n = len(s)
    nzn = sum(1 for r in s if (r.get("A8ED50") or 0) != 0
              and r.get("read_status") == "ok")
    res["a8ed50_nonzero_ratio_full"] = round(nzn / n, 5) if n else None
    res["a8ed50_nz_n"] = nzn
    res["a8ed50_n"] = n
    res.update(anchors(s))
    res["trip"] = d
    return res


def main():
    rep = {"note": "k/N=3 pre-registered; single trips labelled; NO "
                   "significance language; mechanical anchors only"}
    rows = [trip_stats(d) for d, _cfg, _n in TRIPS]
    rep["trips"] = rows

    kn = {}
    for arm, spec in KN.items():
        if arm == "C4":
            # run a = green, evidenced by out-level TRIP_RESULT_C4.json
            # (14:09:16) + TAG-suffixed screenshots; its ndjson was lost in
            # the D5 accident.  Runs b (CRASH, clean dir) and c (green, clean
            # dir) have full evidence.
            rs = [{"trip": "trip_C4(run a, out TRIP_RESULT_C4.json)",
                   "terminal": None, "outcome": "VALID_WINDOW_target_reached"}]
            rs += [trip_stats(d) for d in ("trip_C4_b", "trip_C4_c")]
            k = sum(1 for r in rs
                    if r.get("terminal") == "engine_internal_error_dialog")
            n = len(rs)
        else:
            rs = [trip_stats(d) for d in spec["dirs"]]
            k = sum(1 for r in rs
                    if r.get("terminal") == "engine_internal_error_dialog") \
                + spec["manual_crash_runs"]
            n = len(spec["dirs"]) + spec["manual_crash_runs"]
        kn[arm] = {"N": n, "k_crash": k,
                   "manual_crash_runs": spec.get("manual_crash_runs", 0),
                   "note": spec.get("note"),
                   "per_trip": [{"trip": r.get("trip"),
                                 "terminal": r.get("terminal"),
                                 "outcome": r.get("outcome")} for r in rs]}
    for arm, d in SINGLE.items():
        r = trip_stats(d)
        kn[arm] = {"N": 1,
                   "k_crash": 1 if r.get("terminal") == "engine_internal_error_dialog" else 0,
                   "per_trip": [{"trip": d, "terminal": r.get("terminal"),
                                 "outcome": r.get("outcome")}]}
    rep["k_over_N"] = kn

    # ---- pre-registered paired comparison: C6 vs CTRL_C6 ----
    c6 = trip_stats("trip_C6")
    ctl = trip_stats("trip_CTRL_C6")
    pair = {"combat": {"trip": "trip_C6", "T_end": c6.get("ingame_s")},
            "control": {"trip": "trip_CTRL_C6", "T_end": ctl.get("ingame_s")}}
    if c6.get("full_window") and ctl.get("full_window"):
        tend = min(c6["ingame_s"] or 150.0, ctl["ingame_s"] or 150.0)
        # recompute on the matched window [0, tend]
        s6 = samples_of(load_ndjson(OUT / "trip_C6" / "run.ndjson"))
        sc = samples_of(load_ndjson(OUT / "trip_CTRL_C6" / "run.ndjson"))
        w6 = window_rate([r for r in s6 if r["elapsed_ingame_s"] <= tend])
        wc = window_rate([r for r in sc if r["elapsed_ingame_s"] <= tend])
        nz6 = sum(1 for r in s6 if r["elapsed_ingame_s"] <= tend
                  and (r.get("A8ED50") or 0) != 0 and r.get("read_status") == "ok")
        nzc = sum(1 for r in sc if r["elapsed_ingame_s"] <= tend
                  and (r.get("A8ED50") or 0) != 0 and r.get("read_status") == "ok")
        pair["window_s"] = round(tend, 3)
        pair["combat_rate_pct"] = w6["rate_pct"]
        pair["control_rate_pct"] = wc["rate_pct"]
        ratio = (w6["rate_pct"] / wc["rate_pct"]) if wc["rate_pct"] else None
        pair["ratio_combat_over_control"] = round(ratio, 4) if ratio else None
        pair["combat_a8ed50_nonzero_ratio"] = round(
            nz6 / max(1, sum(1 for r in s6 if r["elapsed_ingame_s"] <= tend
                             and r.get("read_status") == "ok")), 5)
        pair["control_a8ed50_nonzero_ratio"] = round(
            nzc / max(1, sum(1 for r in sc if r["elapsed_ingame_s"] <= tend
                             and r.get("read_status") == "ok")), 5)
        if ratio is not None:
            if ratio < 1.10:
                pair["verdict"] = ("本配置下未观测到与交战成比例的负载抬升"
                                   "（比值 %.3f < 1.10）" % ratio)
            else:
                pair["verdict"] = "初估抬升 %.1f%%（比值 %.3f）" % (
                    (ratio - 1) * 100, ratio)
    rep["paired_control_pre_registered"] = pair

    out = OUT / "analysis.json"
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=2, default=str),
                   encoding="utf-8")
    print(json.dumps({"k_over_N": kn, "paired": pair}, ensure_ascii=False,
                     indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
