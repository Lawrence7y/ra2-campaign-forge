# -*- coding: utf-8 -*-
"""Probe 3: within-trip, time-aligned test of units vs instantaneous fps.

Uses frame_edges (t, frame) at 500 Hz to build per-second fps, and counters at 1 Hz
for unit counts, then correlates them INSIDE one trip. Within-trip control removes
map / harness / BOOT / session as confounders -- only elapsed time and its correlates vary.

Restricting to l3_1101v4c first because it is the one trip where fps rises across all
three windows (18.5 -> 28.4 -> 30.7) with the same map and harness.

Read-only. Prints to stdout.
"""
import json
import os

ROOT = (
    "D:/Project/ra2-campaign-forge/out/re_work/work_chain/"
    "CONTINUE_20261003/lead/qc161_u0400_trip"
)


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


def spear(xs, ys):
    """Spearman = Pearson on ranks (no scipy dependency)."""
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    return pearson(rank(xs), rank(ys))


def load(trip, widx):
    path = os.path.join(ROOT, trip, "measure_w%d.json" % widx)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def per_second_fps(data, edges):
    """frames advanced per 1-second bin, keyed by integer second since first edge.

    frame_edges is a list of [frame, t] pairs (frame first -- verified on disk).
    """
    if not edges:
        return {}
    t0 = edges[0][1]
    bins = {}
    for pair in edges:
        frame, t = pair[0], pair[1]
        k = int(t - t0)
        bins.setdefault(k, []).append(frame)
    out = {}
    for k, frames in bins.items():
        out[k] = frames[-1] - frames[0] if len(frames) >= 2 else 0
    return out


def analyse(trip):
    print("=" * 78)
    print("TRIP %s" % trip)
    print("=" * 78)
    all_u, all_f = [], []
    for widx in (0, 1, 2):
        path = os.path.join(ROOT, trip, "measure_w%d.json" % widx)
        if not os.path.exists(path):
            continue
        data = load(trip, widx)
        counters = data.get("counters") or []
        edges = data.get("frame_edges") or []
        sec = per_second_fps(data, edges)
        if not counters or not sec:
            print("  w%d: no counters/edges" % widx)
            continue
        print("  w%d  units(first,last)=(%s,%s)  fps_avg=%.2f  secbins=%d" %
              (widx, counters[0].get("units"), counters[-1].get("units"),
               (data.get("stats") or {}).get("fps_avg") or -1, len(sec)))

        # align: counter i covers second index i (counters are 1 Hz from window start)
        pts = []
        for i, c in enumerate(counters):
            if i in sec and c.get("units") is not None:
                pts.append((sec[i], c["units"]))
        if len(pts) >= 5:
            fps_v = [p[0] for p in pts]
            u_v = [p[1] for p in pts]
            print("      n=%-3d r(fps,units)=%+.4f  rho=%+.4f   fps[%.0f..%.0f]  units[%d..%d]" %
                  (len(pts), pearson(fps_v, u_v), spear(fps_v, u_v),
                   min(fps_v), max(fps_v), min(u_v), max(u_v)))
            all_u.extend(u_v)
            all_f.extend(fps_v)
        else:
            print("      too few aligned points (%d)" % len(pts))

    if len(all_u) >= 5:
        print("  POOLED across windows: n=%-3d r=%+.4f  rho=%+.4f" %
              (len(all_u), pearson(all_f, all_u), spear(all_f, all_u)))
    print()


def main():
    for trip in ("l3_1101v4c", "l3_1101v4d", "l1a_20261020", "l3_20261023r"):
        if os.path.isdir(os.path.join(ROOT, trip)):
            analyse(trip)


main()
