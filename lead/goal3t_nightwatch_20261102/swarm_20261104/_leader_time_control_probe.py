# -*- coding: utf-8 -*-
"""Probe 4: is the pooled fps-vs-units correlation an artifact of time?

Probe 3 found pooled r=-0.86 for l3_1101v4c, but within-window r was ~0 for w0 and w2.
That pattern is the signature of pooling across windows (Simpson's paradox): across
windows fps rises AND units fall, so pooling manufactures a correlation that the
per-window data does not contain.

This probe adds the decisive control: correlate BOTH variables against TIME inside
each window. If fps~time and units~time are both strong, then fps~units is spurious
(both are just time trends).

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


def load(trip, widx):
    with open(os.path.join(ROOT, trip, "measure_w%d.json" % widx), encoding="utf-8") as fh:
        return json.load(fh)


def per_second(data):
    edges = data.get("frame_edges") or []
    if not edges:
        return {}
    t0 = edges[0][1]
    bins = {}
    for pair in edges:
        k = int(pair[1] - t0)
        bins.setdefault(k, []).append(pair[0])
    return {k: (v[-1] - v[0] if len(v) >= 2 else 0) for k, v in bins.items()}


def analyse(trip):
    print("=" * 80)
    print("TRIP %s -- time control" % trip)
    print("=" * 80)
    print("  window |  r(fps,units)  r(fps,t)  r(units,t) | verdict")
    print("  -------+---------------------------------------+---------------------------")
    for widx in (0, 1, 2):
        path = os.path.join(ROOT, trip, "measure_w%d.json" % widx)
        if not os.path.exists(path):
            continue
        data = load(trip, widx)
        counters = data.get("counters") or []
        sec = per_second(data)
        pts = []
        for i, c in enumerate(counters):
            if i in sec and c.get("units") is not None:
                pts.append((i, sec[i], c["units"]))
        if len(pts) < 5:
            print("  w%d     | too few points (%d)" % (widx, len(pts)))
            continue
        t = [p[0] for p in pts]
        f = [p[1] for p in pts]
        u = [p[2] for p in pts]
        r_fu = pearson(f, u)
        r_ft = pearson(f, t)
        r_ut = pearson(u, t)
        # A confound exists when both variables track time. Flag it explicitly.
        if abs(r_ft) > 0.5 and abs(r_ut) > 0.5:
            verdict = "CONFOUNDED by time -- r(fps,units) unreliable"
        elif abs(r_fu) > 0.5:
            verdict = "candidate real within-window link"
        else:
            verdict = "no within-window link"
        print(
            "  w%d     |    %+.3f        %+.3f     %+.3f   | %s"
            % (widx, r_fu, r_ft, r_ut, verdict)
        )
    print()


def main():
    for trip in ("l3_1101v4c", "l3_1101v4d", "l1a_20261020", "l3_20261023r", "l1c_20261021"):
        if os.path.isdir(os.path.join(ROOT, trip)):
            analyse(trip)


main()
