#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""NEXT_RE_20261112_R02 / W14 —— 节拍准时性离线分析（对 out\\run.ndjson 重算）。

分析（预设判据，与 tick_probe.py 的 predeclared_analysis_plan 一致，不得事后改）：
 §1 实测采样间隔（phase=ingame、read_status=ok 的相邻 t_mono_ns 差）：
    min/中位/p90/p99/max + 直方图；中位 >20 ms ⇒ 高频未达成 ⇒ 只能降级判定。
 §2 frame 递增事件：对每次 frame 增大记录相对时刻、与上次递增的间隔 ms、Δframe，
    写 out\\increments.csv（列含括号采样间隔与 hiccup 标注）。
 §3 饿死判据：间隔 ≥64 ms 的事件数（=至少错过一拍）；相邻两拍 Δframe≥2 的次数
    （区分「采样器 hiccup 无法区分」与「引擎侧跳拍」）；最长间隔及发生时刻、
    当时 win_foreground/mode。
 §4 栅格说明：正常递增间隔落在 [32, 32+采样间隔) ms；32–40 ms 是量化产物非超时。
 §5 对照：W12/W13 的 30 ms 读数（常量内嵌）。
另：零输入证据（ui_watch 的 GetLastInputInfo 在有效段内的变化）；读失败计数；
    整段速率（计数/s，非 FPS）交叉核对 ≈31.25。

用法：python -X utf8 analyze_ticks.py [--ndjson out\\run.ndjson]
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

W14 = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W14_tick_timeliness")
OUT = W14 / "out"

# W12/W13 参照（HANDOFF.md 已复算确认，常量内嵌，不得改动）
W12_REF = {
    "runs": {"R1": 31.2548, "R2": 31.2450, "R3": 31.2484, "R4": 31.2498},
    "repeat_band_pct": 0.02,
    "sampling_ms": 30,
    "note": "W12 为 125s 门控窗口口径；其 163.5s 原始记录开头含 13.028s 加载期停推",
}
W13_REF = {
    "ingame_s": 496.68,
    "beats": 16263,
    "rate_first_third": 31.2435,
    "rate_last_third": 31.2410,
    "drift_pct": 0.0082,
    "stall_ge_1s_in_game": 0,
    "sampling_ms": 30,
    "note": "W13 有效段口径=截到最后一个 frame>0；30ms 采样对 ≤64ms 饿死结构性盲",
}

GAP_STARCVE_MS = 64.0      # ≥64ms = 至少错过一拍（预设）
HICCUP_X = 3.0             # hiccup 判定：括号采样间隔 > max(3×中位, 24ms)
HICCUP_MIN_MS = 24.0
GAP_BUCKETS = [(0, 32), (32, 36), (36, 40), (40, 48), (48, 56), (56, 64),
               (64, 72), (72, 96), (96, 128), (128, float("inf"))]
SI_BUCKETS = [(0, 6), (6, 7), (7, 8), (8, 10), (10, 15), (15, 20), (20, 30),
              (30, float("inf"))]


def pct(sorted_vals, q):
    """线性插值百分位，q∈[0,100]。"""
    n = len(sorted_vals)
    if n == 0:
        return None
    if n == 1:
        return float(sorted_vals[0])
    pos = (n - 1) * q / 100.0
    lo = int(pos)
    hi = min(lo + 1, n - 1)
    frac = pos - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def stats_of(vals):
    if not vals:
        return {"n": 0}
    s = sorted(vals)
    return {"n": len(s), "min": round(min(s), 3),
            "p10": round(pct(s, 10), 3), "median": round(pct(s, 50), 3),
            "p90": round(pct(s, 90), 3), "p99": round(pct(s, 99), 3),
            "max": round(max(s), 3),
            "mean": round(statistics.fmean(s), 3)}


def bucketize(vals, buckets):
    out = []
    for lo, hi in buckets:
        cnt = sum(1 for v in vals if lo <= v < hi)
        out.append({"bucket": "[%s,%s)" % (lo, "∞" if hi == float("inf") else hi),
                    "count": cnt})
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--ndjson", default=str(OUT / "run.ndjson"))
    a = ap.parse_args()
    nd = Path(a.ndjson)

    samples, events, meta_rows, meta_end = [], [], [], None
    with nd.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            k = rec.get("kind")
            if k == "sample":
                samples.append(rec)
            elif k == "event":
                events.append(rec)
            elif k == "meta":
                meta_rows.append(rec)
            elif k == "meta_end":
                meta_end = rec

    res = {"ndjson": str(nd), "n_lines_samples": len(samples),
           "n_events": len(events), "meta_end": meta_end}

    # ---------- 有效局内段 ----------
    ingame_ok = [s for s in samples
                 if s.get("phase") == "ingame" and s.get("read_status") == "ok"]
    ingame_fail = [s for s in samples
                   if s.get("phase") == "ingame" and s.get("read_status") != "ok"]
    post_start_ok = [s for s in samples
                     if s.get("phase") == "post_start" and s.get("read_status") == "ok"]
    res["segment"] = {
        "ingame_ok": len(ingame_ok), "ingame_fail": len(ingame_fail),
        "post_start_ok": len(post_start_ok),
        "first_frame_positive_event": next(
            (e for e in events if e.get("event") == "first_frame_positive"), None),
        "sampling_end_event": next(
            (e for e in events if e.get("event") == "sampling_end"), None),
    }
    if not ingame_ok:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        (OUT / "analysis.json").write_text(
            json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        return

    ingame_ok.sort(key=lambda s: s["t_mono_ns"])
    t0 = ingame_ok[0]["t_mono_ns"]
    t1 = ingame_ok[-1]["t_mono_ns"]
    dur_s = (t1 - t0) / 1e9
    res["segment"]["ingame_window_s"] = round(dur_s, 3)
    res["segment"]["t0_utc"] = ingame_ok[0].get("t_utc_iso")
    res["segment"]["t1_utc"] = ingame_ok[-1].get("t_utc_iso")
    res["segment"]["verdict_data_sufficient"] = dur_s >= 90.0

    # ---------- §1 实测采样间隔 ----------
    si = []
    prev = None
    for s in ingame_ok:
        if prev is not None:
            si.append((s["t_mono_ns"] - prev) / 1e6)
        prev = s["t_mono_ns"]
    si_stats = stats_of(si)
    si_stats["buckets"] = bucketize(si, SI_BUCKETS)
    si_stats["over_20ms_count"] = sum(1 for v in si if v > 20.0)
    si_stats["over_20ms_pct"] = round(
        100.0 * si_stats["over_20ms_count"] / len(si), 3) if si else None
    high_freq_achieved = bool(si_stats["n"] and si_stats["median"] <= 20.0)
    res["sample_intervals_ms"] = si_stats
    res["high_freq_achieved"] = high_freq_achieved

    # 调度健康（sched_late_ms / cadence_resync 事件）
    res["cadence"] = {
        "sched_late_ms": stats_of([float(s["sched_late_ms"]) for s in ingame_ok
                                   if s.get("sched_late_ms") is not None]),
        "n_resync_events": sum(1 for e in events
                               if e.get("event") == "cadence_resync"),
    }

    # ---------- §2+§3 递增事件 ----------
    inc_rows = []          # (idx, t_rel_s, gap_ms, delta_frame, ...)
    starve_events = []     # gap ≥ 64
    multi_events = []      # Δframe ≥ 2
    resets = []            # frame 回退（不应发生在局内）
    prev_frame = None
    prev_sample = None
    last_inc = None        # (t_mono_ns, frame)
    inc_idx = 0
    delta_per_sample = {"0": 0, "1": 0, "2+": 0}
    for s in ingame_ok:
        fr = s.get("frame")
        if fr is None:
            continue
        if prev_frame is not None:
            d = fr - prev_frame
            if d > 0:
                if d == 1:
                    delta_per_sample["1"] += 1
                elif d >= 2:
                    delta_per_sample["2+"] += 1
                inc_idx += 1
                t_rel = (s["t_mono_ns"] - t0) / 1e9
                gap_ms = ((s["t_mono_ns"] - last_inc[0]) / 1e6
                          if last_inc else None)
                bracket_ms = s.get("interval_ms_actual")
                row = {"idx": inc_idx, "t_rel_s": round(t_rel, 4),
                       "gap_ms": (round(gap_ms, 3) if gap_ms is not None else None),
                       "delta_frame": d,
                       "t_utc": s.get("t_utc_iso"),
                       "bracket_sample_ms": (round(bracket_ms, 3)
                                             if bracket_ms is not None else None),
                       "win_foreground": s.get("win_foreground"),
                       "mode_A8B238": s.get("mode_A8B238"),
                       "frame": fr}
                inc_rows.append(row)
                if gap_ms is not None and gap_ms >= GAP_STARCVE_MS:
                    starve_events.append(row)
                if d >= 2:
                    hiccup = (bracket_ms is not None
                              and bracket_ms > max(HICCUP_X * (si_stats["median"]
                                                               or 0),
                                                   HICCUP_MIN_MS))
                    row2 = dict(row)
                    row2["bracket_hiccup_flag"] = bool(hiccup)
                    row2["classification"] = ("sampling_hiccup_undecidable"
                                              if hiccup else "engine_multi_beat")
                    multi_events.append(row2)
                last_inc = (s["t_mono_ns"], fr)
            elif d < 0:
                resets.append({"t_rel_s": round((s["t_mono_ns"] - t0) / 1e9, 4),
                               "from": prev_frame, "to": fr,
                               "t_utc": s.get("t_utc_iso")})
            elif d == 0:
                delta_per_sample["0"] += 1
        prev_frame = fr
        prev_sample = s

    gaps = [r["gap_ms"] for r in inc_rows if r["gap_ms"] is not None]
    gap_stats = stats_of(gaps)
    gap_stats["buckets"] = bucketize(gaps, GAP_BUCKETS)
    gap_stats["ge_64_count"] = len(starve_events)
    gap_stats["ge_56_lt_64_count"] = sum(1 for g in gaps if 56.0 <= g < 64.0)
    gap_stats["ge_40_lt_64_count"] = sum(1 for g in gaps if 40.0 <= g < 64.0)
    grid_note = ("正常递增间隔落在栅格 [32, 32+中位采样间隔) ms；"
                 "32–40ms 实测值是量化产物，不是超时")
    gap_stats["grid_note"] = grid_note

    # 最长间隔明细
    longest = None
    if gaps:
        mx = max(gaps)
        longest = next(r for r in inc_rows if r["gap_ms"] == mx)
    res["increments"] = {
        "n_events": len(inc_rows),
        "gap_ms": gap_stats,
        "delta_per_sample": delta_per_sample,
        "first_increment": inc_rows[0] if inc_rows else None,
        "last_increment": inc_rows[-1] if inc_rows else None,
        "resets_inside_ingame": resets,
    }
    res["starvation"] = {
        "threshold_ms": GAP_STARCVE_MS,
        "ge_64_events": starve_events,
        "ge_64_count": len(starve_events),
        "multi_delta_events": multi_events,
        "multi_delta_count": len(multi_events),
        "multi_delta_engine_count": sum(
            1 for m in multi_events
            if m["classification"] == "engine_multi_beat"),
        "multi_delta_hiccup_count": sum(
            1 for m in multi_events
            if m["classification"] == "sampling_hiccup_undecidable"),
        "longest_gap": longest,
    }

    # ---------- 整段速率交叉核对 ----------
    if inc_rows:
        f_first, f_last = ingame_ok[0]["frame"], ingame_ok[-1]["frame"]
        rate = (f_last - f_first) / dur_s if dur_s > 0 else None
        res["rate_crosscheck"] = {
            "frame_first": f_first, "frame_last": f_last,
            "duration_s": round(dur_s, 3),
            "counts_per_s": round(rate, 4) if rate is not None else None,
            "unit_note": "计数/s（32ms 定拍），非 FPS",
        }

    # ---------- 零输入证据（ui_watch） ----------
    ui_watch = []
    ui_path = OUT / "ui_watch.ndjson"
    if ui_path.exists():
        with ui_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("kind") == "ui_watch":
                    ui_watch.append(rec)
    input_changes = []
    if ui_watch:
        base_li = ui_watch[0].get("last_input_dwtime")
        for r in ui_watch:
            li = r.get("last_input_dwtime")
            if li is not None and base_li is not None and li != base_li:
                input_changes.append({"t_mono_ns": r["t_mono_ns"],
                                      "t_utc_iso": r.get("t_utc_iso"),
                                      "from": base_li, "to": li,
                                      "fg": r.get("win_foreground")})
                base_li = li
    # 只关心有效局内窗口内的输入变化
    in_window = [c for c in input_changes
                 if t0 <= c["t_mono_ns"] <= t1]
    res["zero_input_evidence"] = {
        "ui_watch_scans": len(ui_watch),
        "input_changes_total": len(input_changes),
        "input_changes_inside_ingame_window": in_window,
        "note": "GetLastInputInfo 为系统级最后输入时刻；有效段内任何变化 ⇒ "
                "外部输入发生，须在报告中标注受影响时段",
    }

    # ---------- 分档（预设，四选一） ----------
    if dur_s < 90.0:
        verdict = "[数据不足]"
    elif not high_freq_achieved:
        verdict = "[分辨率不足]"
    elif res["starvation"]["ge_64_count"] == 0 \
            and res["starvation"]["multi_delta_engine_count"] == 0:
        verdict = "[节拍准时]"
    else:
        verdict = "[观测到节拍饿死]"
    res["verdict"] = verdict
    res["verdict_rule"] = ("四选一：高频达成(中位≤20ms)且无≥64ms间隔且无引擎跳拍⇒"
                           "[节拍准时]；出现≥64ms或引擎跳拍⇒[观测到节拍饿死]；"
                           "中位>20ms⇒[分辨率不足]（不得说准时）；有效段<90s⇒[数据不足]")

    # ---------- §5 对照（常量） ----------
    res["w12_w13_reference"] = {"W12": W12_REF, "W13": W13_REF}

    # ---------- increments.csv ----------
    csv_path = OUT / "increments.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["idx", "t_rel_s", "gap_ms", "delta_frame", "frame",
                    "bracket_sample_ms", "win_foreground", "mode_A8B238",
                    "t_utc"])
        for r in inc_rows:
            w.writerow([r["idx"], r["t_rel_s"], r["gap_ms"], r["delta_frame"],
                        r["frame"], r["bracket_sample_ms"], r["win_foreground"],
                        r["mode_A8B238"], r["t_utc"]])
    res["increments_csv"] = str(csv_path)

    (OUT / "analysis.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1, default=str),
        encoding="utf-8")

    # ---------- stdout 摘要 ----------
    print("=== W14 tick timeliness analysis ===")
    print("verdict: %s" % verdict)
    print("segment: ingame_ok=%d fail=%d window=%.2fs data_sufficient=%s" %
          (len(ingame_ok), len(ingame_fail), dur_s,
           res["segment"]["verdict_data_sufficient"]))
    print("sample_intervals_ms: %s" %
          {k: v for k, v in si_stats.items() if k != "buckets"})
    print("high_freq_achieved: %s (median<=20ms)" % high_freq_achieved)
    print("increments: n=%d gap_stats=%s" %
          (len(inc_rows), {k: v for k, v in gap_stats.items()
                           if k not in ("buckets", "grid_note")}))
    print("starvation: ge64=%d multi=%d (engine=%d hiccup=%d) longest=%s" %
          (res["starvation"]["ge_64_count"],
           res["starvation"]["multi_delta_count"],
           res["starvation"]["multi_delta_engine_count"],
           res["starvation"]["multi_delta_hiccup_count"],
           (longest or {}).get("gap_ms")))
    print("rate_crosscheck: %s" % res.get("rate_crosscheck"))
    print("zero_input: scans=%d changes_in_window=%d" %
          (len(ui_watch), len(in_window)))
    print("delta_per_sample: %s" % delta_per_sample)
    print("resets_inside_ingame: %s" % resets)
    print("increments.csv -> %s" % csv_path)
    return res


if __name__ == "__main__":
    main()
