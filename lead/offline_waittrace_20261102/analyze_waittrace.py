"""Offline H8 wait-trace analysis. Reads JSON only; never launches a game.

Two named metrics prevent silently changing the historical ledger's indexing.
Neither metric distinguishes uniformly slow frames from actual hitches.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys


def runs(values, predicate):
    start = None
    for i in range(len(values) + 1):
        hit = i < len(values) and predicate(values[i])
        if hit and start is None:
            start = i
        elif not hit and start is not None:
            yield start, i
            start = None


def summary(values):
    if not values:
        return None
    ordered = sorted(values)
    return {"count": len(values), "median_s": statistics.median(values),
            "p90_floor_s": ordered[int(.9 * (len(values) - 1))],
            "max_s": max(values)}


def episodes(ts, fs, deltas, threshold):
    found = []
    for start, end in runs(deltas, lambda value: value == 0):
        stop = min(end, len(ts) - 1)
        duration = ts[stop] - ts[start]
        if duration >= threshold:
            found.append({"start_s": ts[start], "end_s": ts[stop],
                          "duration_s": duration, "frame": fs[start]})
    return found


def analyze(data, threshold=.1, gap_threshold=.01):
    samples = data.get("samples")
    if not isinstance(samples, list) or len(samples) < 2:
        raise ValueError("samples must contain at least two [time, frame] pairs")
    for row in samples:
        if not isinstance(row, list) or len(row) != 2:
            raise ValueError("invalid sample pair")
        t, f = row
        if (isinstance(t, bool) or not isinstance(t, (int, float))
                or not math.isfinite(t) or t < 0):
            raise ValueError("sample time must be finite and nonnegative")
        if f is not None and (type(f) is not int or f < 0):
            raise ValueError("frame must be a nonnegative integer or null")
    ts, fs = map(list, zip(*samples))
    intervals = [b - a for a, b in zip(ts, ts[1:])]
    if min(intervals) < 0 or ts[-1] <= ts[0]:
        raise ValueError("sample times must be nondecreasing with positive span")
    deltas = [None if a is None or b is None else b - a
              for a, b in zip(fs, fs[1:])]
    histogram = {"read_failure": 0, "zero": 0, "one": 0, "two": 0,
                 "jump_gt_two": 0, "rollback": 0}
    for value in deltas:
        key = ("read_failure" if value is None else "rollback" if value < 0
               else "zero" if value == 0 else "one" if value == 1
               else "two" if value == 2 else "jump_gt_two")
        histogram[key] += 1
    first = next((i + 1 for i, v in enumerate(deltas)
                  if v is not None and v > 0), None)
    warnings = ["Frame plateaus do not distinguish slow cadence from hitches.",
                "Zero failed reads does not exclude missed or delayed polling."]
    result = {"schema_version": 1, "samples": len(samples),
              "source_verdict": data.get("verdict"), "source_n": data.get("n"),
              "source_wait_s": data.get("wait_s"),
              "poll_intervals": summary(intervals),
              "poll_hz_intervals_per_span": (len(ts) - 1) / (ts[-1] - ts[0]),
              "read_failure_samples": fs.count(None), "delta_histogram": histogram,
              "sampling_gaps": {"threshold_s": gap_threshold,
                                "count": sum(v > gap_threshold for v in intervals),
                                "span_upper_bound_s": sum(v for v in intervals if v > gap_threshold)},
              "threshold_s": threshold, "warnings": warnings, "battle": None}
    if first is None:
        result["status"] = "no_advance"
        return result
    if histogram["rollback"] or ts[-1] <= ts[first]:
        result["status"] = "rollback_requires_segmentation" if histogram["rollback"] else "no_battle_span"
        warnings.append("No aggregate battle ratio: invalid span or counter rollback.")
        return result
    bts, bfs = ts[first:], fs[first:]
    span = bts[-1] - bts[0]
    # Historical code aligns the incoming delta with the current sample.
    # Preserve that exact definition under a separate, explicit name.
    legacy = episodes(bts, bfs, deltas[first - 1:], threshold)
    # Here each delta describes the outgoing edge of its indexed sample.
    # A run [s,e) therefore covers equal-frame samples s..e, excluding the
    # final interval to the next changed frame. Nulls break equal-frame runs.
    canonical = episodes(bts, bfs, deltas[first:], threshold)
    def aggregate(items):
        total = sum(item["duration_s"] for item in items)
        return {"count": len(items), "total_s": total, "ratio": total / span,
                "episodes": items}
    advances = [ts[i + 1] for i, v in enumerate(deltas)
                if i + 1 >= first and v is not None and v > 0]
    result["status"] = "ok_with_read_failures" if fs.count(None) else "ok"
    result["battle"] = {"first_advance_index": first,
                        "first_advance_t_rel_s": ts[first],
                        "pre_advance_observed_span_s": ts[first] - ts[0],
                        "span_s": span,
                        "net_frames": None if bfs[-1] is None else bfs[-1] - bfs[0],
                        "legacy_incoming_delta": aggregate(legacy),
                        "equal_frame_sample_span": aggregate(canonical),
                        "advance_intervals": summary([b - a for a, b in zip(advances, advances[1:])]),
                        "last_advance_s": advances[-1],
                        "tail_without_advance_s": ts[-1] - advances[-1]}
    if result["sampling_gaps"]["count"]:
        warnings.append("Sampling gaps are upper bounds; their internal frame history is unknown.")
    return result


def positive_finite(value):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise argparse.ArgumentTypeError("must be positive and finite")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="+", type=Path)
    parser.add_argument("--threshold", type=positive_finite, default=.1)
    parser.add_argument("--gap-threshold", type=positive_finite, default=.01)
    args = parser.parse_args()
    reports = []
    try:
        for path in args.traces:
            raw = path.read_bytes()
            report = analyze(json.loads(raw), args.threshold, args.gap_threshold)
            reports.append({"path": str(path.resolve()),
                            "sha256": hashlib.sha256(raw).hexdigest(), **report})
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(reports, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
