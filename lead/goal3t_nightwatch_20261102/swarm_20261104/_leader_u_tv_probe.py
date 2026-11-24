# -*- coding: utf-8 -*-
"""Probe 2: unit-count total variation (sum of |delta|) vs fps_avg, within-trip focus.

Span (max-min) is a poor churn measure: it ignores how often and how far counts move.
Total variation TV = sum(|c[i]-c[i-1]|) over the 1 Hz counter series captures both.
Read-only; prints to stdout.
"""
import glob
import json
import os

ROOT = (
    "D:/Project/ra2-campaign-forge/out/re_work/work_chain/"
    "CONTINUE_20261003/lead/qc161_u0400_trip"
)


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def tv(series):
    return sum(abs(series[i] - series[i - 1]) for i in range(1, len(series)))


def row_of(trip, widx, path):
    data = load(path)
    counters = data.get("counters") or []
    stats = data.get("stats") or {}
    if len(counters) < 3:
        return None
    u = [c["units"] for c in counters if c.get("units") is not None]
    g = [c["g"] for c in counters if c.get("g") is not None]
    if len(u) < 3:
        return None
    return {
        "trip": trip,
        "w": widx,
        "fps_avg": stats.get("fps_avg"),
        "p50": stats.get("fps_p50"),
        "lf": stats.get("logic_frames"),
        "u_first": u[0],
        "u_last": u[-1],
        "u_span": max(u) - min(u),
        "u_tv": tv(u),
        "u_dist": len(set(u)),
        "g_tv": tv(g) if len(g) >= 3 else None,
        "g_first": g[0] if g else None,
        "g_last": g[-1] if g else None,
    }


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    dx = sum((a - mx) ** 2 for a in xs) ** 0.5
    dy = sum((b - my) ** 2 for b in ys) ** 0.5
    return num / (dx * dy) if dx and dy else float("nan")


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
                r = row_of(trip, idx, path)
            except Exception:  # noqa: BLE001
                continue
            if r and r["fps_avg"] is not None:
                rows.append(r)

    print("=== A. within-trip l3_1101v4c (same map/harness, fps rises across windows) ===")
    for r in rows:
        if r["trip"] == "l3_1101v4c":
            print(
                "  v4c/w%d  fps_avg=%-6.2f  u_first=%-4d u_last=%-4d u_span=%-3d u_tv=%-4d "
                "u_dist=%-3d  g_tv=%s"
                % (r["w"], r["fps_avg"], r["u_first"], r["u_last"], r["u_span"],
                   r["u_tv"], r["u_dist"], r["g_tv"])
            )

    print()
    print("=== B. same, for every trip that has >=2 measurable windows ===")
    by_trip = {}
    for r in rows:
        by_trip.setdefault(r["trip"], []).append(r)
    for trip, rs in sorted(by_trip.items()):
        if len(rs) < 2:
            continue
        rs.sort(key=lambda x: x["w"])
        cells = "  ".join(
            "w%d avg=%.1f u_tv=%d" % (x["w"], x["fps_avg"], x["u_tv"]) for x in rs
        )
        print("  %-20s %s" % (trip, cells))

    print()
    print("=== C. pooled correlations (u_tv as churn measure) ===")
    fps = [r["fps_avg"] for r in rows]
    print("  r(fps_avg, u_tv)   = %.4f   n=%d" % (pearson([r["u_tv"] for r in rows], fps), len(rows)))
    print("  r(fps_avg, u_span) = %.4f" % pearson([r["u_span"] for r in rows], fps))
    print("  r(fps_avg, u_first)= %.4f" % pearson([r["u_first"] for r in rows], fps))

    print()
    print("=== D. split by family (archive_T* vs everything else) ===")
    for fam, pred in (
        ("archive_T*", lambda t: t.startswith("archive_T")),
        ("l3_1101v*", lambda t: t.startswith("l3_1101v")),
        ("l3_2026*", lambda t: t.startswith("l3_2026")),
        ("l1*", lambda t: t.startswith("l1")),
    ):
        sub = [r for r in rows if pred(r["trip"])]
        if len(sub) < 3:
            print("  %-12s n=%d (too few)" % (fam, len(sub)))
            continue
        f = [r["fps_avg"] for r in sub]
        print(
            "  %-12s n=%-3d r(u_tv)=%+.4f  r(u_first)=%+.4f  fps[min..max]=%.1f..%.1f"
            % (
                fam,
                len(sub),
                pearson([r["u_tv"] for r in sub], f),
                pearson([r["u_first"] for r in sub], f),
                min(f),
                max(f),
            )
        )


main()
