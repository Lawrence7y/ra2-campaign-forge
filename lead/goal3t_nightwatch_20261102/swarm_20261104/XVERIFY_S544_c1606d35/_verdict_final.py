# -*- coding: utf-8 -*-
"""汇总员补充复算：目标①样本分层 / T34 停摆结构 / 慢窗终局证据 / 相关与共线敏感性。"""
import json, glob, os, math, statistics
from collections import Counter, defaultdict

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
OUT = "D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35"
paths = [p for p in sorted(glob.glob(ROOT + "/**/measure_w*.json", recursive=True)) if "l3_1101v4h" not in p]

def load(p):
    with open(p, "r", encoding="utf-8") as f: return json.load(f)

def phi(a, b, c, d):
    den = math.sqrt((a+b)*(c+d)*(a+c)*(b+d))
    return (a*d-b*c)/den if den else None

def pearson(xs, ys):
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    sxy = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    sxx = sum((x-mx)**2 for x in xs); syy = sum((y-my)**2 for y in ys)
    return sxy/math.sqrt(sxx*syy) if sxx and syy else None

rows = []
for p in paths:
    j = load(p); st = j.get("stats") or {}; s = j.get("samples") or {}
    t = s.get("t") or []; f = s.get("f") or []; fe = j.get("frame_edges") or []
    g = j.get("gate") or {}
    rel = os.path.relpath(p, ROOT).replace("\\", "/")
    trip = j.get("trip_id") or (rel.split("/")[0] if "/" in rel else "(TRIP_ROOT)")
    tripdir = rel.split("/")[0] if "/" in rel else "(TRIP_ROOT)"
    span = t[-1]-t[0] if len(t) >= 2 else 0.0
    logic = int(f[-1])-int(f[0]) if len(f) >= 2 else 0
    avg = logic/span if span > 0 and logic > 0 else None
    live = None; tail = None
    if len(fe) >= 2:
        dt = fe[-1][1]-fe[0][1]; df = fe[-1][0]-fe[0][0]
        live = df/dt if dt > 0 else None
        tail = t[-1]-fe[-1][1]
    lp = ROOT + "/" + tripdir + "/_launch_result.json"
    sha = json.load(open(lp, encoding="utf-8")).get("harness_sha16") if os.path.isfile(lp) else None
    rows.append(dict(rel=rel, trip=trip, tripdir=tripdir, span_s=j.get("span_s"), span=span,
                     avg=avg, live=live, tail=tail, p50=st.get("fps_p50"),
                     stall=st.get("max_stall_s"), units0=g.get("units0"), pre=g.get("pre_fps15"),
                     verdict=j.get("verdict"), lf=st.get("logic_frames"), map=(j.get("map_sha256") or "")[:16],
                     v4=(sha == "38244d2907e7f7fa"), sha=sha))

comp = [r for r in rows if r["avg"] is not None and r["live"] is not None]
slow = [r for r in comp if r["avg"] < 28]
print("=== HEADLINE COUNTS (103 snapshot) ===")
print("FILES", len(rows), "COMPUTABLE", len(comp), "HEALTHY", len(comp)-len(slow), "SLOW", len(slow))
print("SLOW_SPAN_S", Counter(r["span_s"] for r in slow))
print("SLOW_P50_GE28", sum(1 for r in slow if r["p50"] and r["p50"] >= 28))
print("SLOW_P50_LT28", sum(1 for r in slow if r["p50"] and r["p50"] < 28))

print("\n=== TARGET-1 USABLE SAMPLE TIERS ===")
t25 = [r for r in slow if r["span_s"] == 25.0]
print("TIER_25s_SLOW_WINDOWS", len(t25), "TRIPS", len(set(r["trip"] for r in t25)))
sust = [r for r in t25 if r["p50"] is not None and r["p50"] < 28 and (r["stall"] or 0) < 1.0]
print("TIER_TRUE_SUSTAINED_SLOW_WINDOWS", len(sust), "TRIPS", len(set(r["trip"] for r in sust)))
print("TRUE_SLOW_TRIPS", sorted(set(r["tripdir"] for r in sust)))
stall25 = [r for r in t25 if r["p50"] is not None and r["p50"] >= 28]
print("TIER_STALL_DOMINATED_25s", len(stall25), "TRIPS", len(set(r["trip"] for r in stall25)))
bytrip = defaultdict(list)
for r in rows: bytrip[r["tripdir"]].append(r)
zeroafter = 0
for r in stall25:
    later = [x for x in bytrip[r["tripdir"]] if x["lf"] == 0]
    if later: zeroafter += 1
    print("  STALL", r["rel"], "avg=%.4f" % r["avg"], "live=%.4f" % r["live"],
          "p50=%.4f" % r["p50"], "max_stall=%.6f" % r["stall"],
          "tail=%.6f" % (r["tail"] or 0), "later_zero_windows", len(later))
print("STALL_TRIPS_WITH_LATER_ZERO_ADVANCE", zeroafter, "/", len(stall25))
noadv = [r for r in slow if r["span_s"] == 4.0]
print("EXCLUDED_4s_NO_ADVANCE", len(noadv), [(r["rel"], r["verdict"], r["units0"]) for r in noadv])

print("\n=== §544 NAMED 6 WINDOWS: tail stall / gap ===")
named = ["l3_1101v4d/measure_w0.json", "l3_1101v4e/measure_w0.json", "l3_1101v4e/measure_w1.json",
         "l1c_20261021/measure_w0.json", "l3_20261031hb/measure_w0.json", "l3_20261031hb/measure_w1.json"]
for rel in named:
    r = next(x for x in rows if x["rel"] == rel)
    d = abs(r["avg"]-r["live"])
    print("  ", rel, "avg=%.6f live=%.6f |diff|=%.6f" % (r["avg"], r["live"], d),
          "max_stall=%.6f" % r["stall"], "tail=%.6f" % (r["tail"] or 0),
          "units0=%s map=%s" % (r["units0"], r["map"]))

print("\n=== CORRELATION / PHI SENSITIVITY ===")
valid = [r for r in comp if r["units0"] is not None and r["pre"] is not None and r["live"] > 0]
print("VALID_N", len(valid), "TRIPS", len(set(r["trip"] for r in valid)))
for tag, sel in [("ALL", valid), ("UNITS0>0", [r for r in valid if r["units0"] > 0]),
                 ("UNITS0>=800", [r for r in valid if r["units0"] >= 800]),
                 ("25s", [r for r in valid if r["span_s"] == 25.0])]:
    print("  RHO_PRE_LIVE", tag, len(sel), "%.16f" % pearson([r["pre"] for r in sel], [r["live"] for r in sel]))
bt = defaultdict(list)
for r in valid: bt[r["trip"]].append(r)
tx = [sum(x["pre"] for x in g)/len(g) for g in bt.values()]
ty = [sum(x["live"] for x in g)/len(g) for g in bt.values()]
print("  RHO_PRE_LIVE_TRIPMEAN", len(tx), "%.16f" % pearson(tx, ty))
print("  RHO_UNITS_LIVE_ALL", "%.16f" % pearson([r["units0"] for r in valid], [r["live"] for r in valid]))
print("  RHO_UNITS_LIVE_UNITS0>0", "%.16f" % pearson([r["units0"] for r in valid if r["units0"] > 0],
                                                     [r["live"] for r in valid if r["units0"] > 0]))
for tag, lo, hi in [("BAND_1180_1360", 1180, 1360), ("WIDE_GE800", 800, 1e9)]:
    band = [r for r in valid if r["units0"] is not None and lo <= r["units0"] <= hi]
    fa = [r for r in band if r["live"] >= 28]; sl = [r for r in band if r["live"] < 15]
    a = sum(1 for r in fa if r["v4"]); b = len(fa)-a
    c = sum(1 for r in sl if r["v4"]); d = len(sl)-c
    print("  PHI", tag, "n_band", len(band), "2x2", (a, b, c, d), "%.6f" % phi(a, b, c, d))
    sl28 = [r for r in band if r["live"] < 28]
    a2 = a; b2 = b; c2 = sum(1 for r in sl28 if r["v4"]); d2 = len(sl28)-c2
    print("  PHI", tag, "slow<28", "2x2", (a2, b2, c2, d2), "%.6f" % phi(a2, b2, c2, d2))
print("  V4_WITHIN_VERSION_RANGE", [round((x["live"] or 0), 4) for x in rows if x["tripdir"] == "l3_1101v4c"])

print("\n=== T34 / STALL-DOMINATED SAMPLE GAP CHECK ===")
for rel in ["archive_T34/measure_w0.json", "archive_T32/measure_w0.json", "archive_T38/measure_w1.json"]:
    j = load(ROOT + "/" + rel); t = j["samples"]["t"]; f = j["samples"]["f"]
    dts = [t[i]-t[i-1] for i in range(1, len(t))]
    print("  ", rel, "n", len(t), "dt_sum", round(sum(dts), 9), "dt_max_us", round(max(dts)*1e6, 3),
          "dt_gt_10ms", sum(1 for x in dts if x > 0.010), "gap_sum", sum(x for x in dts if x > 0.010),
          "f", (f[0], f[-1]), "stored_stall", j["stats"]["max_stall_s"])

print("\n=== NONCOMPUTABLE 40 BREAKDOWN ===")
z = i = w = 0
for r in rows:
    if r["avg"] is not None and r["live"] is not None: continue
    p = ROOT + "/" + r["rel"]; j = load(p); s = j.get("samples") or {}
    t = s.get("t") or []; lf = (j.get("stats") or {}).get("logic_frames")
    if len(t) < 2: i += 1
    elif lf is not None and lf < 0: w += 1
    else: z += 1
print("  ZERO_ADVANCE", z, "INSUFFICIENT_SAMPLES", i, "COUNTER_WRAP", w, "TOTAL", z+i+w)

print("\nDONE")
