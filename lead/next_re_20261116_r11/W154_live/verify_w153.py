#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lead's independent spot-check of W153's two headline claims.

Claim A: the ledger's r(bullets, ms/frame) = 0.921 is NOT a cross-segment
         correlation over the corpus; pooled over all trips it is ~0.07.
Claim B: a stronger, trip-paired statistic exists: within each trip,
         windows with bullets >= 75 are slower than windows with bullets < 25,
         in ~19 trips, median ~ +40 ms.

Computation is deliberately independent of W153's scripts:
  window = fixed 10 s slice on t_monotonic; ms/frame = 1000*dT/dframe.
"""
import glob
import json
import os
import statistics
import sys

W = 10.0


def windows(path):
    rows = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("kind") != "sample":
                continue
            t, fr, b = r.get("t_monotonic"), r.get("frame"), r.get("A8ED50")
            if t is None or fr is None or b is None:
                continue
            rows.append((t, fr, b))
    out = []
    if len(rows) < 20:
        return out
    t0 = rows[0][0]
    bucket = {}
    for t, fr, b in rows:
        k = int((t - t0) // W)
        bucket.setdefault(k, []).append((t, fr, b))
    for k in sorted(bucket):
        s = bucket[k]
        if len(s) < 10:
            continue
        if s[-1][0] - s[0][0] < W * 0.6:
            continue
        df = s[-1][1] - s[0][1]
        dt = s[-1][0] - s[0][0]
        if df <= 0 or dt <= 0:
            continue
        out.append((k, df / dt * 1000.0 / 1.0, 1000.0 * dt / df,
                    statistics.fmean(x[2] for x in s)))
    return out


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return None if dx == 0 or dy == 0 else num / (dx * dy)


def main():
    root = r"D:\Project\ra2-campaign-forge\lead"
    files = sorted(glob.glob(os.path.join(root, "**", "run.ndjson"), recursive=True))
    files = [f for f in files if os.path.getsize(f) > 1_000_000]
    print("trips found: %d" % len(files))

    all_b, all_ms = [], []
    pairs = []
    usable = 0
    for f in files:
        try:
            ws = windows(f)
        except Exception as e:
            print("  skip %s : %s" % (os.path.basename(f), e))
            continue
        if not ws:
            continue
        usable += 1
        for _k, _fps, ms, b in ws:
            all_b.append(b)
            all_ms.append(ms)
        hi = [ms for _k, _f, ms, b in ws if b >= 75]
        lo = [ms for _k, _f, ms, b in ws if b < 25]
        if hi and lo:
            pairs.append((os.path.basename(os.path.dirname(f)),
                          statistics.median(hi), statistics.median(lo),
                          statistics.median(hi) - statistics.median(lo)))

    print("trips with usable windows: %d   windows: %d" % (usable, len(all_ms)))
    r = pearson(all_b, all_ms)
    print("\n[Claim A] pooled r(bullets, ms/frame) over ALL windows = %s"
          % ("%.4f" % r if r is not None else "n/a"))
    print("          (ledger's published value: 0.921)")

    print("\n[Claim B] trip-paired: median(ms | bullets>=75) - median(ms | bullets<25)")
    for name, him, lom, d in pairs:
        print("  %-40s hi=%7.2f lo=%7.2f diff=%+7.2f" % (name[:40], him, lom, d))
    if pairs:
        ds = [p[3] for p in pairs]
        print("  trips=%d  positives=%d  median=%+.2f  min=%+.2f  max=%+.2f"
              % (len(ds), sum(1 for d in ds if d > 0), statistics.median(ds), min(ds), max(ds)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
