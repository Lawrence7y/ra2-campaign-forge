"""V1 independent recomputation of MEASURE_V1 windows.

No live game process is started or read. All inputs are read-only JSON / Python
source under the absolute paths below. Outputs are printed to stdout only.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

TRIP = Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")
HARNESS = Path("D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py")


def pctl(sorted_vals: list[float], q: float) -> float | None:
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    idx = (len(sorted_vals) - 1) * q
    lo = int(idx)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = idx - lo
    return float(sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac)


def recompute(payload: dict) -> dict:
    s = payload.get("samples") or {}
    t = [float(v) for v in s.get("t", [])]
    f = [int(v) for v in s.get("f", [])]
    r = {
        "schema": payload.get("schema"),
        "trip_id": payload.get("trip_id"),
        "verdict": payload.get("verdict"),
        "span_s_field": payload.get("span_s"),
        "n_samples": min(len(t), len(f)),
        "len_t": len(t), "len_f": len(f),
        "t_monotonic": all(t[i + 1] >= t[i] for i in range(len(t) - 1)),
        "fps_avg": None, "fps_p50": None, "frame_ms_p50": None,
        "live_fps": None, "n_edges": 0, "n_multi_advance": 0,
        "logic_frames": None, "measured_span": None,
        "edge_span": None, "edge_delta_frames": None,
        "max_stall_s": None,
        "gap_dt_gt_10ms_count": 0,
        "gap_dt_gt_10ms_sum_s": 0.0,
        "gap_dt_gt_10ms_excess_s": 0.0,
        "gap_dt_gt_10ms_max_s": 0.0,
        "stored_fps_avg": (payload.get("stats") or {}).get("fps_avg"),
        "stored_fps_p50": (payload.get("stats") or {}).get("fps_p50"),
        "stored_n_edges": (payload.get("stats") or {}).get("n_edges"),
        "stored_frame_edges_len": len(payload.get("frame_edges") or []),
        "stored_max_stall_s": (payload.get("stats") or {}).get("max_stall_s"),
        "note": "",
    }
    if len(t) != len(f) or len(t) < 2:
        r["note"] = "missing_or_short_samples"
        return r
    span = t[-1] - t[0]
    logic = f[-1] - f[0]
    r["measured_span"] = span
    r["logic_frames"] = logic
    if span > 0 and logic > 0:
        r["fps_avg"] = logic / span

    stored_fe = payload.get("frame_edges") or []
    edges: list[tuple[int, float]] = []
    if stored_fe and len(stored_fe) >= 2:
        # frame_edges is the exact first-observation edge table persisted by the
        # harness. Its t values are rounded to 6 decimals (same as samples.t).
        edges = [(int(e[0]), float(e[1])) for e in stored_fe]
    else:
        # Fallback for legacy/error windows: rebuild from raw samples.
        prev_f: int | None = None
        for tv, fv in zip(t, f):
            if prev_f is None or fv != prev_f:
                edges.append((fv, tv))
                prev_f = fv
    r["n_edges"] = len(edges)

    # Check persisted edges against raw samples (rounded t, exact f).
    rebuilt: list[tuple[int, float]] = []
    prev_f = None
    for tv, fv in zip(t, f):
        if prev_f is None or fv != prev_f:
            rebuilt.append((fv, tv))
            prev_f = fv
    r["edge_table_matches_samples"] = (rebuilt == edges)

    # Same D-1 frame_ms construction as harness _measure_stats.
    frame_ms: list[float] = []
    n_multi = 0
    for (fa, ta), (fb, tb) in zip(edges, edges[1:]):
        df = fb - fa
        if df == 1:
            frame_ms.append((tb - ta) * 1000.0)
        elif df > 1:
            n_multi += 1
    r["n_multi_advance"] = n_multi
    frame_ms.sort()
    p50 = pctl(frame_ms, 0.50)
    r["frame_ms_p50"] = p50
    if p50 is not None and p50 > 0:
        r["fps_p50"] = 1000.0 / p50

    # The exact live_fps formula specified by this V1 ask, using first/last edges.
    if len(edges) >= 2:
        df_edge = edges[-1][0] - edges[0][0]
        dt_edge = edges[-1][1] - edges[0][1]
        r["edge_delta_frames"] = df_edge
        r["edge_span"] = dt_edge
        if dt_edge > 0 and df_edge > 0:
            r["live_fps"] = df_edge / dt_edge

    # Longest consecutive df=0 wall-clock run (same estimator as _measure_stats).
    run_t0, run_f = t[0], f[0]
    best = 0.0
    for tv, fv in zip(t[1:], f[1:]):
        if fv != run_f:
            if tv - run_t0 > best:
                best = tv - run_t0
            run_t0, run_f = tv, fv
    if t[-1] - run_t0 > best:
        best = t[-1] - run_t0
    r["max_stall_s"] = best

    # Sampling gaps: strict dt > 10 ms; report both total dt and excess over 10 ms.
    for i in range(len(t) - 1):
        dt = t[i + 1] - t[i]
        if dt > 0.010:
            r["gap_dt_gt_10ms_count"] += 1
            r["gap_dt_gt_10ms_sum_s"] += dt
            r["gap_dt_gt_10ms_excess_s"] += dt - 0.010
            if dt > r["gap_dt_gt_10ms_max_s"]:
                r["gap_dt_gt_10ms_max_s"] = dt
    return r


def num(v: float | None, digits: int = 6) -> str:
    return "NA" if v is None else f"{v:.{digits}f}"


def close(a: float | None, b: float | None, tol: float = 1e-6) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= tol


def main() -> None:
    files = sorted(TRIP.rglob("measure_w*.json"))
    print(f"TRIP={TRIP.as_posix()}")
    print(f"HARNESS={HARNESS.as_posix()}")
    print(f"TOTAL_FILES={len(files)}")
    print(f"ROOT_LEVEL_FILES={len([p for p in files if p.parent == TRIP])}")
    print(f"SUBDIR_FILES={len([p for p in files if p.parent != TRIP])}")
    print(f"HARNESS_EXISTS={HARNESS.is_file()}")

    rows: list[dict] = []
    bad_shape: list[str] = []
    mismatches: list[str] = []
    for p in files:
        payload = json.loads(p.read_text(encoding="utf-8"))
        r = recompute(payload)
        r["path"] = p.relative_to(TRIP).as_posix()
        if r["path"].find("/") < 0:
            r["path"] = "./" + r["path"]
        rows.append(r)
        if r["len_t"] != r["len_f"] or not r["t_monotonic"]:
            bad_shape.append(r["path"])
        st = payload.get("stats") or {}
        # Stats in JSON were computed from unrounded in-memory t; samples.t are rounded
        # to 6 decimals, so use a small absolute tolerance.
        for key, stored in (
            ("fps_avg", st.get("fps_avg")),
            ("fps_p50", st.get("fps_p50")),
        ):
            tol = 1e-5 if key == "fps_avg" else 0.01
            if not close(r[key], stored, tol):
                mismatches.append(f"{r['path']} {key}: recomputed={r[key]!r} stored={stored!r} tol={tol}")
            if r["n_edges"] != st.get("n_edges"):
                mismatches.append(f"{r['path']} n_edges: recomputed={r['n_edges']} stored={st.get('n_edges')!r}")
        if not r.get("edge_table_matches_samples", False):
            mismatches.append(f"{r['path']} frame_edges != rebuilt edge table from samples")

        if not close(r["max_stall_s"], st.get("max_stall_s"), 3e-6):
            mismatches.append(f"{r['path']} max_stall_s: recomputed={r['max_stall_s']!r} stored={st.get('max_stall_s')!r}")

    print(f"BAD_SHAPE={len(bad_shape)} {bad_shape}")
    print(f"STATS_OR_EDGE_MISMATCHES={len(mismatches)}")
    for line in mismatches[:40]:
        print("MISMATCH " + line)

    nominal_spans: dict[str, int] = {}
    for r in rows:
        key = repr(r["span_s_field"])
        nominal_spans[key] = nominal_spans.get(key, 0) + 1
    print(f"NOMINAL_SPAN_S_DISTRIBUTION={nominal_spans}")

    computable = [r for r in rows if r["live_fps"] is not None]
    skipped = [r for r in rows if r["live_fps"] is None]
    print(f"WINDOWS_WITH_COMPUTABLE_ADVANCE={len(computable)}")
    print(f"WINDOWS_WITHOUT_COMPUTABLE_ADVANCE={len(skipped)}")
    print("SKIPPED_REASONS:")
    for r in skipped:
        print(f"  {r['path']} samples={r['n_samples']} logic_frames={r['logic_frames']} edges={r['n_edges']} verdict={r['verdict']} note={r['note']}")

    spans = [r["measured_span"] for r in computable if r["measured_span"] is not None]
    if spans:
        print(f"MEASURED_SPAN_MIN_MAX=({min(spans):.6f}, {max(spans):.6f})")
        nominal_25 = [r["measured_span"] for r in computable if r["span_s_field"] == 25.0 and r["measured_span"] is not None]
        if nominal_25:
            print(f"NOMINAL_25S_MEASURED_SPAN_MIN_MAX=({min(nominal_25):.6f}, {max(nominal_25):.6f}) COUNT={len(nominal_25)}")

    print()
    print("FULL_TABLE (recomputed from raw samples.t/samples.f; all windows with computable live_fps)")
    print("path\tfps_avg\tlive_fps\tfps_p50\tlogic_frames\tmeasured_span_s\tedge_span_s\tmax_stall_s\tgap_gt10ms_sum_s")
    for r in computable:
        print(
            f"{r['path']}\t{num(r['fps_avg'])}\t{num(r['live_fps'])}\t{num(r['fps_p50'])}\t"
            f"{r['logic_frames']}\t{num(r['measured_span'])}\t{num(r['edge_span'])}\t"
            f"{num(r['max_stall_s'])}\t{num(r['gap_dt_gt_10ms_sum_s'])}"
        )

    mixed = [r for r in computable if r["fps_avg"] is not None and r["fps_avg"] < 28 and r["fps_p50"] is not None and r["fps_p50"] >= 28]
    live_low = [r for r in computable if r["live_fps"] < 28]
    p50_low = [r for r in computable if r["fps_p50"] is not None and r["fps_p50"] < 28]
    p50_none = [r for r in computable if r["fps_p50"] is None]
    avg_low = [r for r in computable if r["fps_avg"] is not None and r["fps_avg"] < 28]
    print()
    print(f"THRESHOLD=28 COMPUTABLE_DENOMINATOR={len(computable)}")
    print(f"FPS_AVG_LT_28_COUNT={len(avg_low)}")
    print(f"FPS_AVG_LT_28_AND_FPS_P50_GE_28_COUNT={len(mixed)}")
    for r in mixed:
        print(
            f"  MIXED {r['path']} fps_avg={num(r['fps_avg'])} live_fps={num(r['live_fps'])} "
            f"fps_p50={num(r['fps_p50'])} max_stall_s={num(r['max_stall_s'])} "
            f"gap_gt10ms_sum_s={num(r['gap_dt_gt_10ms_sum_s'])} edge_span_s={num(r['edge_span'])}"
        )
    print(f"LIVE_FPS_LT_28_COUNT={len(live_low)}")
    for r in live_low:
        print(f"  LIVE_LOW {r['path']} live_fps={num(r['live_fps'])} fps_avg={num(r['fps_avg'])} fps_p50={num(r['fps_p50'])}")
    print(f"FPS_P50_LT_28_COUNT={len(p50_low)}")
    for r in p50_low:
        print(f"  P50_LOW {r['path']} fps_p50={num(r['fps_p50'])} fps_avg={num(r['fps_avg'])} live_fps={num(r['live_fps'])}")
    print(f"FPS_P50_NONE_COUNT={len(p50_none)}")
    for r in p50_none:
        print(f"  P50_NONE {r['path']} edges={r['n_edges']} n_multi={r['n_multi_advance']}")

    t34 = next(r for r in rows if r["path"] == "archive_T34/measure_w0.json")
    print()
    print("ARCHIVE_T34_W0_SPECIAL")
    print(f"path={t34['path']} trip_id={t34['trip_id']} verdict={t34['verdict']} schema={t34['schema']}")
    print(f"n_samples={t34['n_samples']} measured_span_s={num(t34['measured_span'], 9)} span_s_field={t34['span_s_field']}")
    print(f"logic_frames={t34['logic_frames']} fps_avg={num(t34['fps_avg'], 9)} stored_fps_avg={num(t34['stored_fps_avg'], 9)}")
    print(f"frame_ms_p50={num(t34['frame_ms_p50'], 9)} fps_p50={num(t34['fps_p50'], 9)} stored_fps_p50={num(t34['stored_fps_p50'], 9)}")
    print(f"n_edges={t34['n_edges']} edge_delta_frames={t34['edge_delta_frames']} edge_span_s={num(t34['edge_span'], 9)} live_fps={num(t34['live_fps'], 9)}")
    print(f"max_stall_s={num(t34['max_stall_s'], 9)} stored_max_stall_s={num(t34['stored_max_stall_s'], 9)}")
    print(f"gap_dt_gt_10ms_count={t34['gap_dt_gt_10ms_count']}")
    print(f"gap_dt_gt_10ms_sum_s={num(t34['gap_dt_gt_10ms_sum_s'], 9)}")
    print(f"gap_dt_gt_10ms_excess_sum_s={num(t34['gap_dt_gt_10ms_excess_s'], 9)}")
    print(f"gap_dt_gt_10ms_max_s={num(t34['gap_dt_gt_10ms_max_s'], 9)}")


if __name__ == "__main__":
    main()
