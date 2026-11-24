# -*- coding: utf-8 -*-
"""Probe: does unit-count churn (distinct values / range at 1 Hz) track fps_avg?

Read-only. Reads measure_w0.json .. measure_w2.json across every trip dir and
prints one row per window. Writes nothing but stdout.
"""
import glob
import json
import os

ROOT = (
    "D:/Project/ra2-campaign-forge/out/re_work/work_chain/"
    "CONTINUE_20261003/lead/qc161_u0400_trip"
)

FIELDS = ("units", "infantry", "b", "g")


def window_row(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    counters = data.get("counters") or []
    stats = data.get("stats") or {}
    if len(counters) < 2:
        return None
    out = {
        "fps_avg": stats.get("fps_avg"),
        "p50": stats.get("fps_p50"),
        "lf": stats.get("logic_frames"),
        "max_stall": stats.get("max_stall_s"),
        "n": len(counters),
    }
    for key in FIELDS:
        vals = [c.get(key) for c in counters if c.get(key) is not None]
        if not vals:
            out[key] = None
            continue
        out[key] = {
            "first": vals[0],
            "last": vals[-1],
            "span": max(vals) - min(vals),
            "distinct": len(set(vals)),
        }
    return out


def main():
    rows = []
    for trip_dir in sorted(glob.glob(os.path.join(ROOT, "*"))):
        if not os.path.isdir(trip_dir):
            continue
        trip = os.path.basename(trip_dir)
        for idx in (0, 1, 2):
            path = os.path.join(trip_dir, "measure_w%d.json" % idx)
            if not os.path.exists(path):
                continue
            try:
                row = window_row(path)
            except Exception as exc:  # noqa: BLE001 - probe wants to keep going
                print("%-22s w%d  ERR %s" % (trip, idx, str(exc)[:50]))
                continue
            if row is None:
                continue
            rows.append((trip, idx, row))

    header = "%-22s %-3s %-8s %-8s %-6s %-9s %-7s %-7s"
    print(header % ("trip", "w", "fps_avg", "p50", "lf", "maxstall", "u_span", "u_dist"))
    print("-" * 90)
    for trip, idx, row in rows:
        u = row.get("units") or {}
        fps = row.get("fps_avg")
        p50 = row.get("p50")
        print(
            header
            % (
                trip,
                idx,
                "-" if fps is None else "%.2f" % fps,
                "-" if p50 is None else "%.2f" % p50,
                row.get("lf"),
                "-" if row.get("max_stall") is None else "%.2f" % row["max_stall"],
                u.get("span", "-"),
                u.get("distinct", "-"),
            )
        )

    print()
    print("=== correlation probe: fps_avg vs units span / distinct (only windows with fps) ===")
    usable = [r for r in rows if r[2].get("fps_avg") is not None and r[2].get("units")]
    if len(usable) >= 5:
        import statistics

        fps_vals = [r[2]["fps_avg"] for r in usable]
        for metric in ("span", "distinct"):
            xs = [r[2]["units"][metric] for r in usable]
            mx = statistics.fmean(xs)
            my = statistics.fmean(fps_vals)
            num = sum((a - mx) * (b - my) for a, b in zip(xs, fps_vals))
            den = (
                sum((a - mx) ** 2 for a in xs) ** 0.5
                * sum((b - my) ** 2 for b in fps_vals) ** 0.5
            )
            rho = num / den if den else float("nan")
            print("  peason r(fps_avg, units_%s) = %.4f   n=%d" % (metric, rho, len(xs)))

        slow = [r for r in usable if r[2]["fps_avg"] < 28]
        fast = [r for r in usable if r[2]["fps_avg"] >= 28]
        print()
        print("  slow (fps_avg<28): n=%d" % len(slow))
        for r in sorted(slow, key=lambda x: x[2]["fps_avg"]):
            u = r[2]["units"]
            print(
                "    %-22s w%d  avg=%-7.2f  u_span=%-4s u_dist=%-3s b_span=%-3s"
                % (r[0], r[1], r[2]["fps_avg"], u["span"], u["distinct"], r[2]["b"]["span"] if r[2].get("b") else "-")
            )
        print("  fast (fps_avg>=28): n=%d" % len(fast))
        for r in sorted(fast, key=lambda x: -x[2]["fps_avg"]):
            u = r[2]["units"]
            print(
                "    %-22s w%d  avg=%-7.2f  u_span=%-4s u_dist=%-3s b_span=%-3s"
                % (r[0], r[1], r[2]["fps_avg"], u["span"], u["distinct"], r[2]["b"]["span"] if r[2].get("b") else "-")
            )


main()
