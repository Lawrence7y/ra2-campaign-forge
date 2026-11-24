"""Read-only checks requested for FACTBASE; never import project/game code."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--data-root", type=Path, required=True)
parser.add_argument("--output-dir", type=Path, required=True)
args = parser.parse_args()
allowed = Path("D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5")
if not args.data_root.is_absolute() or not args.output_dir.is_absolute():
    raise SystemExit("Absolute paths required")
if args.output_dir.resolve() != allowed.resolve():
    raise SystemExit("Output outside the authorized directory")
base = args.data_root
started = datetime.now(timezone.utc).isoformat()
files = sorted(base.rglob("measure_w*.json"))
snapshot = {p: (p.stat().st_size, p.stat().st_mtime_ns) for p in files}
rows = []
errors = []
selected = None


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


for path in files:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        samples = data.get("samples") or {}
        times, frames = samples.get("t") or [], samples.get("f") or []
        if len(times) != len(frames):
            raise ValueError("samples.t/f length mismatch")
        depth = len(path.relative_to(base).parts) - 1
        layer = "root" if depth == 0 else "child" if depth == 1 else "deeper"
        delta = int(frames[-1]) - int(frames[0]) if len(frames) >= 2 else None
        stats = data.get("stats") or {}
        rows.append({"path": path.as_posix(), "layer": layer, "df": delta,
                     "n": len(times), "avg": stats.get("fps_avg"),
                     "p50": stats.get("fps_p50"), "stall": stats.get("max_stall_s"),
                     "span": data.get("span_s"), "trip_id": data.get("trip_id"),
                     "units0": (data.get("gate") or {}).get("units0"),
                     "verdict": data.get("verdict")})
        if path == base / "archive_T34" / "measure_w0.json":
            selected = (data, times, frames)
    except Exception as exc:
        errors.append({"path": path.as_posix(), "error": repr(exc)})

lines = []


def emit(text):
    lines.append(text)
    print(text)


emit("START_UTC=" + started)
emit("COMMAND=" + " ".join('"' + v + '"' if " " in v else v for v in [sys.executable, "-I", "-X", "utf8", *sys.argv]))
emit("DATA_ROOT=" + base.as_posix())
emit(f"A recursive_total={len(files)} parsed={len(rows)} parse_errors={len(errors)}")
for layer in ("root", "child", "deeper"):
    group = [r for r in rows if r["layer"] == layer]
    emit(f"A {layer}: files={len(group)} df_positive={sum(r['df'] is not None and r['df'] > 0 for r in group)}")
moving = [r for r in rows if r["df"] is not None and r["df"] > 0]
emit(f"A total_df_positive={len(moving)} nonpositive_or_insufficient={len(rows) - len(moving)}")
emit("A root_files=" + json.dumps([{k: r[k] for k in ("path", "trip_id", "df")} for r in rows if r["layer"] == "root"], ensure_ascii=False))


def low_avg(r):
    return number(r["avg"]) and r["avg"] < 28


def low_both(r):
    return low_avg(r) and number(r["p50"]) and r["p50"] < 28


for label, group in (("all", rows), ("25s", [r for r in rows if r["span"] == 25.0]),
                     ("4s", [r for r in rows if r["span"] == 4.0])):
    slow = [r for r in group if low_avg(r)]
    both = [r for r in group if low_both(r)]
    emit(f"B {label}: avg_lt28={len(slow)} avg_and_p50_lt28={len(both)} difference={len(slow)-len(both)}")
positive25 = [r for r in moving if r["span"] == 25.0]
positive4 = [r for r in moving if r["span"] == 4.0]
steady = [r for r in positive25 if low_both(r)]
stopped = [r for r in positive25 if low_avg(r) and number(r["p50"]) and r["p50"] >= 28]
steady_ids = {r["trip_id"] for r in steady}
stopped_ids = {r["trip_id"] for r in stopped}
emit(f"B positive_25s={len(positive25)} positive_4s={len(positive4)} healthy_25s={sum(number(r['avg']) and r['avg'] >= 28 for r in positive25)}")
emit(f"B 25s_low_both: windows={len(steady)} trip_ids={len(steady_ids)} min_stall_s={min(r['stall'] for r in steady):.6f} max_stall_s={max(r['stall'] for r in steady):.6f}")
emit(f"B 25s_low_avg_high_p50: windows={len(stopped)} trip_ids={len(stopped_ids)} trip_overlap={len(steady_ids & stopped_ids)}")
emit("B low_both_trip_ids=" + json.dumps(sorted(steady_ids), ensure_ascii=False))
emit("B positive_4s_files=" + json.dumps([r["path"] for r in positive4], ensure_ascii=False))

if selected is None:
    errors.append({"error": "archive_T34/measure_w0.json not read"})
else:
    data, times, frames = selected
    intervals = [float(b) - float(a) for a, b in zip(times, times[1:])]
    gaps = [dt for dt in intervals if dt > 0.010]
    run_start, run_frame = float(times[0]), frames[0]
    best = (0.0, run_start, run_start, run_frame)
    edges = [(int(frames[0]), float(times[0]))]
    for t, f in zip(times[1:], frames[1:]):
        t = float(t)
        if f != run_frame:
            if t - run_start > best[0]:
                best = (t - run_start, run_start, t, run_frame)
            edges.append((int(f), t))
            run_start, run_frame = t, f
    if float(times[-1]) - run_start > best[0]:
        best = (float(times[-1]) - run_start, run_start, float(times[-1]), run_frame)
    stats = data["stats"]
    measured_span = float(times[-1]) - float(times[0])
    net = int(frames[-1]) - int(frames[0])
    emit("C path=" + (base / "archive_T34" / "measure_w0.json").as_posix())
    emit(f"C n_samples={len(times)} nominal_span_s={data.get('span_s')} measured_span_s={measured_span:.12f} f_first={frames[0]} f_last={frames[-1]} df={net}")
    emit(f"C dt_gt10ms_count={len(gaps)} dt_gt10ms_sum_s={sum(gaps):.12f} dt_max_ms={max(intervals)*1000:.6f} nonpositive_dt={sum(dt <= 0 for dt in intervals)}")
    emit(f"C zero_advance_max_s={best[0]:.12f} rounded_6={round(best[0],6):.6f} stored_max_stall_s={stats.get('max_stall_s')} frame={best[3]} start_rel_s={best[1]-float(times[0]):.12f} end_rel_s={best[2]-float(times[0]):.12f}")
    emit(f"C fps_avg_recomputed={net/measured_span:.12f} stored_fps_avg={stats.get('fps_avg')} stored_fps_p50={stats.get('fps_p50')} edges_recomputed={len(edges)} stored_edges_match={data.get('frame_edges') == [list(e) for e in edges]}")

current_files = sorted(base.rglob("measure_w*.json"))
changed = [p.as_posix() for p in files if not p.exists() or (p.stat().st_size, p.stat().st_mtime_ns) != snapshot[p]]
added = sorted(p.as_posix() for p in set(current_files) - set(files))
emit(f"INTEGRITY changed_or_removed={len(changed)} added={len(added)}")
emit("ERRORS=" + json.dumps(errors, ensure_ascii=False))
emit("END_UTC=" + datetime.now(timezone.utc).isoformat())
(args.output_dir / "factbase_probe_output.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
if errors or changed or added:
    raise SystemExit(1)
