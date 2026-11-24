# -*- coding: utf-8 -*-
"""汇总员独立复算：只读原始 measure_w*.json，不采信任何 lane 的中间产物。"""
import json, glob, os, math, statistics
from collections import Counter, defaultdict

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
OUT = "D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35"

paths = sorted(glob.glob(ROOT + "/**/measure_w*.json", recursive=True))
print("SNAPSHOT_TOTAL_FILES", len(paths))
rootlevel = [p for p in paths if os.path.dirname(p) == ROOT]
print("ROOT_LEVEL_FILES", len(rootlevel), [os.path.basename(p) for p in rootlevel])
print("SUBDIR_FILES", len(paths) - len(rootlevel))
v4h = [p for p in paths if "l3_1101v4h" in p]
print("V4H_FILES", len(v4h), [os.path.basename(p) for p in v4h])

def load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def pctl(v, q):
    if not v: return None
    s = sorted(v); n = len(s)
    if n == 1: return s[0]
    x = (n - 1) * q; lo = int(math.floor(x)); hi = int(math.ceil(x))
    return s[lo] + (s[hi] - s[lo]) * (x - lo)

def pearson(xs, ys):
    assert len(xs) == len(ys)
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    sxy = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    sxx = sum((x-mx)**2 for x in xs); syy = sum((y-my)**2 for y in ys)
    return sxy/math.sqrt(sxx*syy) if sxx > 0 and syy > 0 else None

rows = []
for p in paths:
    d = load(p)
    s = d.get("samples") or {}
    t = s.get("t") or []; f = s.get("f") or []
    fe = d.get("frame_edges")
    st = d.get("stats") or {}; g = d.get("gate") or {}
    trip = d.get("trip_id") or os.path.basename(os.path.dirname(p))
    rel = os.path.relpath(p, ROOT).replace("\\", "/")
    span = (t[-1] - t[0]) if len(t) >= 2 else 0.0
    logic = (int(f[-1]) - int(f[0])) if len(f) >= 2 else 0
    avg = logic/span if span > 0 and logic > 0 else None
    # fps_p50 from df==1 edge intervals
    ms = []
    if fe and len(fe) >= 2:
        for a, b in zip(fe, fe[1:]):
            df = int(b[0]) - int(a[0])
            if df == 1: ms.append((float(b[1]) - float(a[1]))*1000.0)
    p50 = pctl(ms, 0.5); fp50 = 1000.0/p50 if p50 else None
    live = None
    if fe and len(fe) >= 2:
        dt = float(fe[-1][1]) - float(fe[0][1])
        df = int(fe[-1][0]) - int(fe[0][0])
        if dt > 0 and df > 0: live = df/dt
    # my own max stall from samples: longest constant-f run
    max_stall = 0.0
    if len(t) >= 2 and len(f) == len(t):
        start = 0
        for i in range(1, len(f)):
            if f[i] != f[start]:
                max_stall = max(max_stall, t[i]-t[start]); start = i
        max_stall = max(max_stall, t[-1]-t[start])
    # gap >10ms sum
    gap10 = sum((t[i]-t[i-1]) for i in range(1, len(t)) if (t[i]-t[i-1]) > 0.010)
    ngap10 = sum(1 for i in range(1, len(t)) if (t[i]-t[i-1]) > 0.010)
    rows.append(dict(rel=rel, path=p, trip=trip, span_s=d.get("span_s"), span=span,
                     logic=logic, avg=avg, stored_avg=st.get("fps_avg"),
                     p50=fp50, stored_p50=st.get("fps_p50"), live=live,
                     max_stall=max_stall, stored_stall=st.get("max_stall_s"),
                     verdict=d.get("verdict"), note=(st.get("note") or ""),
                     units0=g.get("units0"), pre=g.get("pre_fps15"),
                     gate_ok=g.get("ok"), map_sha=(d.get("map_sha256") or "")[:16],
                     gamemd_sha=(d.get("gamemd_sha256") or "")[:16],
                     n_samples=len(t), n_edges=len(fe) if fe else 0,
                     gap10=gap10, ngap10=ngap10,
                     logic_frames=st.get("logic_frames"),
                     n_multi=st.get("n_multi_advance"),
                     error=d.get("error")))

print("\n=== SNAPSHOT A: all current files ===")
print("TOTAL", len(rows))
print("SPAN_S_DIST", Counter(r["span_s"] for r in rows))
print("VERDICT_DIST", Counter(r["verdict"] for r in rows))
print("MAP_SHA_DISTINCT", len(set(r["map_sha"] for r in rows)))
print("GAMEMD_SHA_DISTINCT", len(set(r["gamemd_sha"] for r in rows)))
comp = [r for r in rows if r["avg"] is not None and r["live"] is not None]
print("COMPUTABLE_ADVANCE", len(comp))
print("NONCOMPUTABLE", len(rows)-len(comp))
print("NONCOMPUTABLE_BREAKDOWN")
for r in rows:
    if r not in comp:
        print("  NC", r["rel"], "verdict", r["verdict"], "span_s", r["span_s"],
              "n_samples", r["n_samples"], "n_edges", r["n_edges"],
              "logic_frames", r["logic_frames"], "note", r["note"], "gate_ok", r["gate_ok"])
print("AVG_VS_STORED_MAXDIFF", max(abs(r["avg"]-r["stored_avg"]) for r in comp))
print("P50_VS_STORED_MAXDIFF", max(abs(r["p50"]-r["stored_p50"]) for r in comp if r["p50"] and r["stored_p50"]))

def report(tag, rs):
    c = [r for r in rs if r["avg"] is not None and r["live"] is not None]
    print("\n=== " + tag + " ===")
    print("N_FILES", len(rs), "N_COMPUTABLE", len(c))
    print("SPANS_25s_COMPUTABLE", sum(1 for r in c if r["span_s"] == 25.0))
    s25 = [r["span"] for r in c if r["span_s"] == 25.0]
    print("SPAN_RANGE_25s", (min(s25), max(s25)) if s25 else None,
          "EXACTLY_25", sum(1 for x in s25 if abs(x-25.0) < 1e-9))
    print("FPS_AVG_LT_28", sum(1 for r in c if r["avg"] < 28))
    mixed = [r for r in c if r["avg"] < 28 and r["stored_p50"] is not None and r["stored_p50"] >= 28]
    print("FPS_AVG_LT_28_AND_STORED_P50_GE_28", len(mixed))
    print("LIVE_FPS_LT_28", sum(1 for r in c if r["live"] < 28))
    print("STORED_P50_LT_28", sum(1 for r in c if r["stored_p50"] is not None and r["stored_p50"] < 28))
    print("LIVE_LT_AVG_COUNT", sum(1 for r in c if r["live"] < r["avg"]))
    print("FPS_AVG_LT_28_FULL_P50_LT_28", sum(1 for r in c if r["avg"] < 28 and r["stored_p50"] is not None and r["stored_p50"] < 28))
    print("MIXED_LIST")
    for r in mixed:
        print("  MIX", r["rel"], "avg=%.6f" % r["avg"], "live=%.6f" % r["live"],
              "p50=%.6f" % r["stored_p50"], "max_stall=%.6f" % r["max_stall"],
              "edge_span=%.6f" % (r["logic"]/r["live"] if r["live"] else 0),
              "span_s", r["span_s"], "units0", r["units0"])
    print("MIXED_LIVE_GE_28", sum(1 for r in mixed if r["live"] >= 28),
          "MIXED_LIVE_LT_28", sum(1 for r in mixed if r["live"] < 28))
    print("MIXED_MAX_STALL_RANGE", (min(r["max_stall"] for r in mixed), max(r["max_stall"] for r in mixed)) if mixed else None)
    print("MIXED_N_MULTI_NONZERO", sum(1 for r in mixed if r["n_multi"]))
    return c

c_all = report("SNAPSHOT A (current)", rows)
# 103-snapshot: drop the post-lane v4h file
rows103 = [r for r in rows if "l3_1101v4h" not in r["rel"]]
c103 = report("SNAPSHOT B (103, exclude l3_1101v4h)", rows103)

# === rho variants ===
valid = [r for r in c103 if r["units0"] is not None and r["pre"] is not None and r["live"] is not None and r["live"] > 0]
print("\n=== RHO on 103 snapshot ===")
print("VALID_N", len(valid), "VALID_TRIPS", len(set(r["trip"] for r in valid)))
print("RHO_PRE_LIVE_ALL", pearson([r["pre"] for r in valid], [r["live"] for r in valid]))
print("RHO_UNITS_LIVE_ALL", pearson([r["units0"] for r in valid], [r["live"] for r in valid]))
v60 = [r for r in valid if r["units0"] > 0]
print("RHO_PRE_LIVE_UNITS0_GT0", len(v60), pearson([r["pre"] for r in v60], [r["live"] for r in v60]))
print("RHO_UNITS_LIVE_UNITS0_GT0", pearson([r["units0"] for r in v60], [r["live"] for r in v60]))
v800 = [r for r in valid if r["units0"] >= 800]
print("RHO_PRE_LIVE_UNITS0_GE800", len(v800), pearson([r["pre"] for r in v800], [r["live"] for r in v800]))
v25 = [r for r in valid if r["span_s"] == 25.0]
print("RHO_PRE_LIVE_25s", len(v25), pearson([r["pre"] for r in v25], [r["live"] for r in v25]))
# trip-level mean dedup
bytrip = defaultdict(list)
for r in valid: bytrip[r["trip"]].append(r)
tx = [sum(x["pre"] for x in g)/len(g) for g in bytrip.values()]
ty = [sum(x["live"] for x in g)/len(g) for g in bytrip.values()]
tu = [sum(x["units0"] for x in g)/len(g) for g in bytrip.values()]
print("RHO_PRE_LIVE_TRIPMEAN", len(tx), pearson(tx, ty))
print("RHO_UNITS_LIVE_TRIPMEAN", pearson(tu, ty))
print("MULTIWINDOW_TRIPS", sum(1 for g in bytrip.values() if len(g) >= 2),
      "PRE_ALL_SAME", sum(1 for g in bytrip.values() if len(set(x["pre"] for x in g)) == 1))
alltrips = defaultdict(list)
for r in rows103: alltrips[r["trip"]].append(r)
print("ALL_TRIPS", len(alltrips), "TRIPS_WITH_3_WINDOWS", sum(1 for g in alltrips.values() if len(g) == 3))
print("ALL_MULTI_TRIPS_PRE_SAME", sum(1 for g in alltrips.values() if len(g) >= 2 and len(set(x["pre"] for x in g)) == 1),
      "ALL_MULTI_TRIPS", sum(1 for g in alltrips.values() if len(g) >= 2))

# === §544 named four timepoints ===
named = ["l3_1101v4d/measure_w0.json", "l3_1101v4e/measure_w0.json", "l3_1101v4e/measure_w1.json",
         "l1c_20261021/measure_w0.json", "l3_20261031hb/measure_w0.json", "l3_20261031hb/measure_w1.json"]
print("\n=== §544 NAMED WINDOWS (recomputed from frame_edges) ===")
for rel in named:
    r = next((x for x in rows103 if x["rel"] == rel), None)
    if not r: print("  MISSING", rel); continue
    d = load(r["path"]); fe = d["frame_edges"]
    df = int(fe[-1][0]) - int(fe[0][0]); dt = float(fe[-1][1]) - float(fe[0][1])
    print("  NAMED", rel, "f0=%s f1=%s df=%d dt=%.6f live=%.6f units0=%s pre=%s avg=%.6f stored_avg=%.6f max_stall=%.6f map=%s" %
          (fe[0][0], fe[-1][0], df, dt, df/dt, r["units0"], r["pre"], r["avg"], r["stored_avg"], r["max_stall"], r["map_sha"]))

# === T34 gap ===
print("\n=== T34 gap ===")
r34 = next(x for x in rows103 if x["rel"] == "archive_T34/measure_w0.json")
d34 = load(r34["path"]); t = d34["samples"]["t"]; f = d34["samples"]["f"]
dts = [t[i]-t[i-1] for i in range(1, len(t))]
print("  n_samples", len(t), "dt_sum", sum(dts), "wall_span", t[-1]-t[0],
      "dt_min_us", min(dts)*1e6, "dt_max_us", max(dts)*1e6,
      "dt_gt_10ms", sum(1 for x in dts if x > 0.010),
      "gap_gt_10ms_sum", sum(x for x in dts if x > 0.010))
runs = []; st = 0
for i in range(1, len(f)):
    if f[i] != f[st]: runs.append((f[st], st, i-1, t[i]-t[st])); st = i
runs.append((f[st], st, len(f)-1, t[-1]-t[st]))
print("  n_runs", len(runs), "last_run", runs[-1], "f_range", (f[0], f[-1]))
print("  stored_avg", r34["stored_avg"], "my_avg", r34["avg"], "live", r34["live"], "p50", r34["stored_p50"])

# === save rows for follow-ups ===
with open(OUT + "/_verdict_census.json", "w", encoding="utf-8") as fo:
    json.dump([{k: v for k, v in r.items() if k != "path"} for r in rows], fo, ensure_ascii=False, indent=1)
print("\nDONE")
