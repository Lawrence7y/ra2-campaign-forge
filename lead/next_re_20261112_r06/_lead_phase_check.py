import json

for trip in ("out/trip_P1/run.ndjson", "out/trip_P2/run.ndjson"):
    rows = [json.loads(l) for l in open(trip, encoding="utf-8") if l.strip()]
    rows = [d for d in rows if d.get("kind") == "sample"]
    a8 = [d.get("A8ED50") or 0 for d in rows]
    xs = [d.get("X87E8E0") for d in rows]
    fr = [d.get("frame") for d in rows]
    ing = [d.get("elapsed_ingame_s") for d in rows]
    nz = sum(1 for v in a8 if v)
    first = next((i for i, v in enumerate(a8) if v), None)
    print("===", trip)
    print("  samples=%d  ingame=%.2f..%.2f s  frame=%s..%s"
          % (len(rows), ing[0] or 0, ing[-1] or 0, fr[0], fr[-1]))
    print("  A8ED50 nonzero=%d/%d  first_idx=%s" % (nz, len(a8), first))
    if first is not None:
        print("    first nonzero at t=%.2f s; last3=%s" % (ing[first] or 0, a8[-3:]))
    else:
        print("    A8ED50 all zero => crash happened with NO bullets (pure movement/pathing)")
    xch = sum(1 for i in range(1, len(xs)) if xs[i] != xs[i - 1])
    print("  X87E8E0 first=%s last=%s changes=%d" % (xs[0], xs[-1], xch))
    print()
