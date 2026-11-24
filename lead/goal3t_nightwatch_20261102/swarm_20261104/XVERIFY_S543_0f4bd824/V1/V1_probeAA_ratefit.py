"""V1 probe AA: independent check of 'screen clock == this match's elapsed logic time'.

For each trip that owns a readable score-screen clock:
 1. take every frame_edges (frame, monotonic t) across ALL its measure windows;
 2. fit the logic-frame rate R by least squares on the edges that advanced
    (R = dFrame/dTime over the advancing span, using first..last advancing edge);
 3. predicted clock = f_last / R  (f_last = the frozen frame number), and compare with the
    seconds read off the PNG in probes I/X.
This uses only the JSON timestamps plus my own pixel reading of the clock.
"""
import os, glob, json
import numpy as np

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

READ = {  # my pixel read of the 时间 field (probe I / X), plus the 2 root shots
    "archive_T33": (738, 24), "archive_T34": (302, 10), "archive_T36": (310, 10),
    "archive_T38": (940, 32), "archive_T39": (945, 31), "archive_T40": (908, 30),
    "archive_T41": (860, 28), "archive_T43": (314, 10), "archive_T44": (883, 29),
    "archive_T45": (845, 28), "archive_T49_u0800": (448, 15), "l3_20261023r": (4367, 176),
    "(root)": (373, 13),
}

print("%-22s %-8s %-9s %-9s %-9s %-9s %-9s %s" % (
    "trip", "f_last", "clock_s", "adv_edges", "R_fit", "pred_s", "diff_s", "note"))
for trip, (flast, cs) in READ.items():
    base = ROOT if trip == "(root)" else ROOT + "/" + trip
    edges = []
    for jf in sorted(glob.glob(base + "/measure_w*.json")):
        d = json.load(open(jf, encoding="utf-8"))
        for e in (d.get("frame_edges") or []):
            edges.append((e[0], e[1]))
    edges.sort(key=lambda x: x[1])
    adv = [(f, t) for (f, t) in edges if True]
    # fit only over the strictly advancing portion
    fs = [f for f, t in adv]
    ts = [t for f, t in adv]
    n_adv = sum(1 for i in range(1, len(fs)) if fs[i] > fs[i - 1])
    if n_adv < 1:
        print("%-22s %-8d %-9d no advancing edges -> cannot fit R" % (trip, flast, cs))
        continue
    i0 = 0
    while i0 < len(fs) - 1 and fs[i0 + 1] <= fs[i0]:
        i0 += 1
    j = len(fs) - 1
    while j > i0 and fs[j] <= fs[i0]:
        j -= 1
    R = (fs[j] - fs[i0]) / (ts[j] - ts[i0])
    pred = flast / R
    print("%-22s %-8d %-9d %-9d %-9.3f %-9.2f %-9.2f %s" % (
        trip, flast, cs, n_adv, R, pred, cs - pred,
        "edges=%d span=%.2fs dF=%d" % (len(fs), ts[j] - ts[i0], fs[j] - fs[i0])))

print()
print("=== same test done the document's way (implied fps = f/clock) ===")
for trip, (flast, cs) in READ.items():
    print("   %-22s f=%-6d clock=%-4d f/clock=%6.2f" % (trip, flast, cs, flast / cs))
