# -*- coding: utf-8 -*-
"""Q02 采窗段抽验：measure_w*.json 的冻结形态（对账 §529「冻结后帧增量=0」）。
只读；stdout-only。
"""
import json
import glob

OUT = []
def p(*a):
    s = " ".join(str(x) for x in a)
    OUT.append(s)
    print(s, flush=True)

files = sorted(glob.glob(
    r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/"
    r"lead/qc161_u0400_trip/**/measure_w*.json", recursive=True))
p("total measure_w*.json found:", len(files))

# pick those whose frame range starts near 900-950 (v4-e session alignment, per reconcile note)
picked = []
for fp in files:
    try:
        d = json.load(open(fp, encoding="utf-8"))
    except Exception as e:
        continue
    S = d.get("samples")
    if not isinstance(S, dict) or "t" not in S or "f" not in S:
        continue
    t, f = S["t"], S["f"]
    if not t:
        continue
    picked.append((fp, d, t, f))

p("parseable:", len(picked))
p("")
p("%-58s %-22s %6s %8s  %s" % ("file", "trip/verdict", "n", "span", "shape"))
for fp, d, t, f in picked:
    n = len(t)
    span = t[-1] - t[0]
    # largest equal-f run
    best = (0, 0, 0)  # dur, start_idx, end_idx
    i = 0
    while i < n:
        j = i
        while j + 1 < n and f[j + 1] == f[i]:
            j += 1
        if t[j] - t[i] > best[0]:
            best = (t[j] - t[i], i, j)
        i = j + 1
    dur, i0, j0 = best
    covers = (j0 - i0 + 1) / n
    tail_frozen = (j0 == n - 1)
    df_total = f[-1] - f[0]
    df_before = f[i0] - f[0]
    flag = ""
    if dur >= 2.0 and covers > 0.5:
        flag = "STALL-DOMINATED"
    p("%-58s %-22s %6d %8.2fs  maxEqRun=%.3fs(cov%.0f%%,tailFrozen=%s) df_total=%d df_before_freeze=%d %s" % (
        fp.split("qc161_u0400_trip")[-1],
        "%s/%s" % (d.get("trip_id", "?"), d.get("verdict", d.get("window", "?"))),
        n, span, dur, 100 * covers, tail_frozen, df_total, df_before, flag))

with open(r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/Q02/Q02_measure_check_out.txt",
          "w", encoding="utf-8") as fh:
    fh.write("\n".join(OUT) + "\n")
