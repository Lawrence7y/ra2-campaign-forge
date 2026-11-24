# -*- coding: utf-8 -*-
"""RECHECK sample 1: independent window census (do NOT reuse leader/V3 code).

Scope: every measure_w*.json under BASE at depth<=2 (trip subdirs + root level).
Classify by frame_edges only. Also: interval census over MOVING windows,
n_multi_advance, and which frozen windows have a window-end PNG on disk.
Read-only. Zero real machine.
"""
import glob
import json
import os
import statistics as st

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

paths = sorted(glob.glob(os.path.join(BASE, "*", "measure_w*.json"))) + \
        sorted(glob.glob(os.path.join(BASE, "measure_w*.json")))
seen = set()
paths = [p for p in paths if not (p in seen or seen.add(p))]

print("measure json found (dedup):", len(paths))
no_edges = []
wins = []
for p in paths:
    j = json.load(open(p, encoding="utf-8"))
    ed = j.get("frame_edges") or []
    if not ed:
        no_edges.append(p)
        continue
    trip = os.path.basename(os.path.dirname(p))
    if trip == os.path.basename(BASE):
        trip = "<root>"
    f0, f1 = ed[0][0], ed[-1][0]
    wins.append(dict(p=p, trip=trip, w=j.get("window"), f0=f0, f1=f1, df=f1 - f0,
                     n=len(ed), edges=ed, span=j.get("span_s"),
                     fps=(j.get("stats") or {}).get("fps_avg"),
                     p50=(j.get("stats") or {}).get("fps_p50"),
                     stall=(j.get("stats") or {}).get("max_stall_s"),
                     verd=j.get("verdict")))

print("json WITHOUT frame_edges:", len(no_edges))
for p in no_edges:
    print("   ", os.path.relpath(p, BASE))
print("windows with edges:", len(wins), " trips:", len({w['trip'] for w in wins}))

adv = [w for w in wins if w["df"] > 0]
frz = [w for w in wins if w["df"] == 0 and w["f0"] != 0]
lz = [w for w in wins if w["df"] == 0 and w["f0"] == 0]
neg = [w for w in wins if w["df"] < 0]
print("CENSUS  df>0=%d  frozen(df==0&f0!=0)=%d  loadfrozen(df==0&f0==0)=%d  df<0=%d  sum=%d"
      % (len(adv), len(frz), len(lz), len(neg), len(adv) + len(frz) + len(lz) + len(neg)))

hi = [w for w in adv if (w["fps"] or 0) >= 28]
lo = [w for w in adv if not ((w["fps"] or 0) >= 28)]
print("adv split: fps_avg>=28 -> %d ; fps_avg<28(or None) -> %d" % (len(hi), len(lo)))
print("  fps None among adv:", [(w["trip"], w["w"]) for w in adv if w["fps"] is None])

print("\n=== frozen windows (df==0, f0!=0) with f0 and end-png presence ===")
for w in sorted(frz, key=lambda x: (x["trip"], x["w"])):
    png = os.path.join(os.path.dirname(w["p"]), "measure_w%s_end_x.png" % w["w"])
    print("  %-20s w%s f0=%-6s span=%-6s verdict=%-16s endpng=%s"
          % (w["trip"], w["w"], w["f0"], w["span"], w["verd"],
             "YES" if os.path.exists(png) else "NO"))
    w["png"] = png
print("  frozen with end png: %d / %d" % (sum(1 for w in frz if os.path.exists(w["png"])), len(frz)))

print("\n=== interval census inside MOVING (df>0) windows ===")
gaps = []
multi = {}
for w in adv:
    e = w["edges"]
    for i in range(1, len(e)):
        dt = e[i][1] - e[i - 1][1]
        dfr = e[i][0] - e[i - 1][0]
        gaps.append((dt, dfr, w["trip"], w["w"], i))
        if dfr != 1:
            k = (w["trip"], w["w"])
            multi.setdefault(k, []).append(dfr)
print("  total intervals in moving windows:", len(gaps))
buckets = [(0, .1), (.1, .2), (.2, .5), (.5, 1.0), (1.0, 2.0), (2.0, 5.0), (5.0, 1e9)]
for a, b in buckets:
    n = sum(1 for g in gaps if a <= g[0] < b)
    print("   %5.1f-%-5.1f s : %6d (%.2f%%)" % (a, b, n, 100.0 * n / len(gaps)))
big = [g for g in gaps if g[0] >= 1.0]
print("  >=1.0s gaps:", len(big))
for g in big:
    print("     %.3fs at %s/w%s idx=%d step=%d" % (g[0], g[2], g[3], g[4], g[1]))
print("  windows with any step != 1:", len(multi))
for k, v in sorted(multi.items(), key=lambda x: -len(x[1])):
    from collections import Counter
    print("     %s/w%s  n_multi=%d steps=%s" % (k[0], k[1], len(v), dict(Counter(v))))

print("\n=== 'long stall share' inside the fps<28 moving windows ===")
for w in sorted(lo, key=lambda x: x["fps"] if x["fps"] is not None else 99):
    share = (w["stall"] / w["span"]) if (w["stall"] and w["span"]) else None
    print("  %-20s w%s df=%-5d fps_avg=%-8s p50=%-8s stall=%-8s share=%s"
          % (w["trip"], w["w"], w["df"], w["fps"], w["p50"], w["stall"],
             ("%.1f%%" % (100 * share)) if share is not None else "n/a"))
