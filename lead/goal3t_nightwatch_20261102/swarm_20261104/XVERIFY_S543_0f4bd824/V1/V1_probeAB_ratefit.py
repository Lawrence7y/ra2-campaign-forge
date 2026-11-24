"""V1 probe AB (replaces AA's broken fit): logic-frame rate R from the JSON timestamps.

Fixes vs probe AA:
 - keep only the windows belonging to the SAME trip_id (the trip root mixes trips),
 - build the strictly increasing subsequence of (frame, t) edges, i.e. drop the frozen tail,
 - R = dFrame/dTime over that increasing part; predicted clock = f_frozen / R.
"""
import os, glob, json

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
READ = {"archive_T33": (738, 24), "archive_T34": (302, 10), "archive_T36": (310, 10),
        "archive_T38": (940, 32), "archive_T39": (945, 31), "archive_T40": (908, 30),
        "archive_T41": (860, 28), "archive_T43": (314, 10), "archive_T44": (883, 29),
        "archive_T45": (845, 28), "archive_T49_u0800": (448, 15), "l3_20261023r": (4367, 176)}
# the two shots at the trip root belong to trip QC161-U0400-T55h (read from their own json)
EXTRA = [("(root) T55h", 373, 13, ["measure_w1.json", "measure_w2.json"], ROOT)]

print("%-20s %-8s %-8s %-10s %-10s %-10s %-10s %s" % (
    "trip", "f_froz", "clock_s", "R_fit", "pred_s", "diff_s", "n_incr", "detail"))
for trip, (ff, cs) in READ.items():
    ev = []
    tid = None
    for jf in sorted(glob.glob(ROOT + "/" + trip + "/measure_w*.json")):
        d = json.load(open(jf, encoding="utf-8"))
        tid = d.get("trip_id")
        for e in (d.get("frame_edges") or []):
            ev.append((e[1], e[0]))
    ev.sort()
    incr, last = [], None
    for t, f in ev:
        if last is None or f > last:
            incr.append((f, t))
            last = f
    if len(incr) < 2:
        print("%-20s no increasing edges" % trip)
        continue
    f0, t0 = incr[0]
    f1, t1 = incr[-1]
    R = (f1 - f0) / (t1 - t0)
    pred = ff / R
    print("%-20s %-8d %-8d %-10.3f %-10.2f %-10.2f %-10d dF=%d over %.3fs (edge0 f=%d -> f=%d)" % (
        trip, ff, cs, R, pred, cs - pred, len(incr), f1 - f0, t1 - t0, f0, f1))

for name, ff, cs, jnames, base in EXTRA:
    ev = []
    for jn in jnames:
        d = json.load(open(base + "/" + jn, encoding="utf-8"))
        for e in (d.get("frame_edges") or []):
            ev.append((e[1], e[0]))
    ev.sort()
    incr, last = [], None
    for t, f in ev:
        if last is None or f > last:
            incr.append((f, t)); last = f
    f0, t0 = incr[0]; f1, t1 = incr[-1]
    if len(incr) < 2 or (t1 - t0) == 0:
        print("%-20s %-8d %-8d  cannot fit R from w1/w2 alone (n_incr=%d)" % (name, ff, cs, len(incr)))
        continue
    R = (f1 - f0) / (t1 - t0)
    print("%-20s %-8d %-8d %-10.3f %-10.2f %-10.2f %-10d dF=%d over %.3fs" % (
        name, ff, cs, R, ff / R, cs - ff / R, len(incr), f1 - f0, t1 - t0))
